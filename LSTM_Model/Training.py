# Import required libraries
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import os
import json
from datetime import datetime
from tensorflow.keras.callbacks import Callback

class BatchProgressCallback(Callback):
    def __init__(self, total_batches_per_epoch=None):
        super(BatchProgressCallback, self).__init__()
        self.total_batches_per_epoch = total_batches_per_epoch
    
    def on_train_begin(self, logs=None):
        print("Début de l'entraînement...")
    
    def on_epoch_begin(self, epoch, logs=None):
        print(f"\nÉpoque {epoch+1}/{self.params['epochs']} :")
    
    def on_train_batch_end(self, batch, logs=None):
        if self.total_batches_per_epoch:
            progress = (batch + 1) / self.total_batches_per_epoch * 100
            print(f"\rBatch {batch+1}/{self.total_batches_per_epoch} - {progress:.1f}% - loss: {logs['loss']:.4f} - accuracy: {logs['accuracy']:.4f}", end="")
        else:
            print(f"\rBatch {batch+1} - loss: {logs['loss']:.4f} - accuracy: {logs['accuracy']:.4f}", end="")
    
    def on_epoch_end(self, epoch, logs=None):
        print(f"\nÉpoque terminée - loss: {logs['loss']:.4f} - accuracy: {logs['accuracy']:.4f} - val_loss: {logs['val_loss']:.4f} - val_accuracy: {logs['val_accuracy']:.4f}")

# File handling
base_folder = "LSTM_Model"
file_name = "M_and_D_sensors_labeled_chunked.json"
file_path = os.path.join(base_folder, file_name)

with open(file_path, 'r') as f:
    M_and_D_sensors_labeled_chunked = json.load(f)

def create_dataset(data, time_steps=10):
    X, y = [], []
    all_sensors = [f"M{i:03d}" for i in range(1, 32)] + ["D001", "D003", "D004"]
    global_active_activities = {}  # Stocke les activités en cours entre les séquences
    last_majority_activity = None  # Stocke la dernière activité majoritaire

    for i in range(0, len(data) - time_steps + 1, time_steps):
        sequence = data[i:i + time_steps]
        activity_line_counts = {}
        active_activities = {activity: 0 for activity in global_active_activities}  # Réinitialise avec start_idx=0

        # --- Début : Traitement des événements "begin" et "end" ---
        for j, event in enumerate(sequence):
            if event["activity"]:
                activity_parts = event["activity"].replace(" ", "").split(",")
                if len(activity_parts) != 2:
                    continue
                activity_name, action = activity_parts

                if action == "begin":
                    active_activities[activity_name] = j  # Début à l'indice j
                elif action == "end":
                    if activity_name in active_activities:
                        start_idx = active_activities[activity_name]
                        duration = j - start_idx + 1
                        activity_line_counts[activity_name] = activity_line_counts.get(activity_name, 0) + duration
                        del active_activities[activity_name]
                    else:
                        # Activité commencée avant cette séquence
                        duration = j + 1
                        activity_line_counts[activity_name] = activity_line_counts.get(activity_name, 0) + duration

        # Gestion des activités non terminées
        for activity, start_idx in active_activities.items():
            duration = time_steps - start_idx
            activity_line_counts[activity] = activity_line_counts.get(activity, 0) + duration

        global_active_activities = active_activities.copy()  # Mise à jour pour les séquences suivantes
        # --- Fin : Traitement des événements ---

        # --- Début : Calcul de l'activité majoritaire ---
        if activity_line_counts:
            majority_activity = max(activity_line_counts.items(), key=lambda x: x[1])[0]
        else:
            if global_active_activities:
                majority_activity = list(global_active_activities.keys())[0]
            else:
                # Aucune activité détectée : utiliser la dernière activité majoritaire
                majority_activity = last_majority_activity if last_majority_activity is not None else "None"

        # Éliminer "None" en utilisant la continuité
        if majority_activity == "None" and last_majority_activity is not None:
            majority_activity = last_majority_activity

        # Mise à jour pour les prochaines séquences
        last_majority_activity = majority_activity
        # --- Fin : Calcul de l'activité majoritaire ---

        # --- Début : Extraction des caractéristiques ---
        # Extraction des caractéristiques temporelles
        try:
            start_dt = datetime.strptime(f"{sequence[0]['date']} {sequence[0]['time']}", "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            start_dt = datetime.strptime(f"{sequence[0]['date']} {sequence[0]['time']}", "%Y-%m-%d %H:%M:%S")

        try:
            end_dt = datetime.strptime(f"{sequence[-1]['date']} {sequence[-1]['time']}", "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            end_dt = datetime.strptime(f"{sequence[-1]['date']} {sequence[-1]['time']}", "%Y-%m-%d %H:%M:%S")

        duration = (end_dt - start_dt).total_seconds()

        # Comptage des capteurs
        sensor_counts = {sensor: sum(1 for e in sequence if e["sensor"] == sensor and e["state"] == "ON") for sensor in all_sensors}
        feature_vector = [start_dt.timestamp(), end_dt.timestamp(), duration] + [sensor_counts[sensor] for sensor in all_sensors]
        # --- Fin : Extraction des caractéristiques ---

        X.append(feature_vector)
        y.append(majority_activity)

    return np.array(X, dtype=np.float32), np.array(y)
def save_dataset_to_file(X, y, filename="dataset_output.txt"):
    with open(filename, 'w') as f:
        for i in range(len(X)):
            # Flatten 2D array to 1D list
            flattened_X = X[i].flatten().tolist()
            f.write(f"X[{i}]:\n    {flattened_X}\n")
            f.write(f"y[{i}]: {y[i]}\n")
            f.write("_" * 50 + "\n\n")

# Main execution
if __name__ == "__main__":
    print("\nStep 1: Data Preparation")
    TEST_SIZE = 0.2

    if not M_and_D_sensors_labeled_chunked:
        print("❌ Error: Data not loaded")
        exit(1)

    print("Creating dataset...")
    X, y = create_dataset(M_and_D_sensors_labeled_chunked  , time_steps=10)
    print(f"Dataset created with {len(X)} sequences")
    print("saving data")
    save_dataset_to_file(X, y, filename="dataset_output.txt")
    print("data saved")
    # Reshape data for LSTM
    time_steps = 1
    X = X.reshape((X.shape[0], time_steps, X.shape[1]))
    
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")

    # Label encoding
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)
    
    # Train-test split
    split_idx = int(len(X) * (1 - TEST_SIZE))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y_encoded[:split_idx], y_encoded[split_idx:]

    print("\nStep 2: Model Building")
    model = Sequential()
    model.add(LSTM(256, activation='tanh', input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True))
    model.add(Dropout(0.3))
    model.add(LSTM(128, activation='tanh'))
    model.add(Dropout(0.3))
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    print("\nStep 3: Model Training")
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        verbose=1
    )

   

    

print("\nTraining complete!")
# Show final training metrics
print(f"Final training loss: {history.history['loss'][-1]:.4f}")
print(f"Final validation loss: {history.history['val_loss'][-1]:.4f}")
print(f"Final training accuracy: {history.history['accuracy'][-1]:.4f}")
print(f"Final validation accuracy: {history.history['val_accuracy'][-1]:.4f}")

# Plot training history
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title("Training Progress - Loss")
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title("Training Progress - Accuracy")
plt.legend()
plt.show()

# --------------------------
print("\nStep 4: Model Evaluation")
# --------------------------
# Generate predictions on test set
test_predictions = model.predict(X_test)
print(f"\nPrediction shape: {test_predictions.shape}")  # Should be (num_test_samples, num_classes)

# Convert from probability distributions to class indices
predicted_classes = np.argmax(test_predictions, axis=1)

# Calculate and display accuracy
accuracy = accuracy_score(y_test, predicted_classes)
print(f"\nAccuracy: {accuracy:.4f}")  # Higher is better

# Show detailed classification report
print(classification_report(
    y_test,
    predicted_classes
))

# Generate confusion matrix
cm = confusion_matrix(y_test, predicted_classes)
plt.figure(figsize=(12, 10))
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.colorbar()
tick_marks = np.arange(len(label_encoder.classes_))
plt.xticks(tick_marks, label_encoder.classes_, rotation=90)
plt.yticks(tick_marks, label_encoder.classes_)
plt.tight_layout()
plt.ylabel('True label')
plt.xlabel('Predicted label')
plt.show()

# Show sample predictions vs actual values
print("\nSample Predictions vs Actuals:")
for i in range(20):
    true_class = label_encoder.classes_[y_test[i]]
    pred_class = label_encoder.classes_[predicted_classes[i]]
    confidence = test_predictions[i][predicted_classes[i]] * 100
    print(f"True: {true_class} | Predicted: {pred_class} | Confidence: {confidence:.2f}%")

# --------------------------
print("\nStep 5: Save Model")
# --------------------------
# Save the model
model.save("lstm_activity_classifier.h5")
print("Model saved as 'lstm_activity_classifier.h5'")

# Save label encoder classes to properly decode predictions later
np.save('activity_classes.npy', label_encoder.classes_)
print("Activity classes saved as 'activity_classes.npy'")

print("\nProcess complete!")