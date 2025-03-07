
"""
updated-cross-validation-with-time-features.py

This file implements a k-fold cross-validation approach for activity recognition using LSTM models and
time-based features. Key functionalities include:

1. Custom metrics: Implements F1 score calculations via callback and metric functions for model evaluation.

2. Model architecture: Creates a bidirectional LSTM network with dropout layers for recognizing activity
   patterns from sensor and time data.

3. Cross-validation: Uses StratifiedKFold to properly handle imbalanced activity classes, running training
   across multiple data splits.

4. Feature standardization: Applies StandardScaler to normalize feature values properly across folds.

5. Training with callbacks: Implements early stopping and learning rate reduction to optimize training.

6. Comprehensive evaluation: Calculates and visualizes accuracy, F1 scores, and loss curves for each fold.

7. Feature importance analysis: Visualizes the importance of different features based on network weights.

8. Model persistence: Saves trained models, scalers, and class labels for future use in deployment.

This script addresses activity recognition as a time-series classification problem, using both sensor 
activation counts and temporal patterns to identify daily activities.
"""
# Import required libraries
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import StratifiedKFold #Better for imbalanced datasets than KFold
import os
from datetime import datetime, timedelta
import json
from datetime import datetime
from tensorflow.keras.callbacks import Callback, EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
import pickle
import math
# Import functions from Create_LSTM_Input.py
from Create_LSTM_Input import encode_cyclical_feature, extract_time_features, create_dataset, save_dataset_to_file
# Custom F1 Score metrics for Keras
class F1ScoreCallback(Callback):
    def __init__(self, validation_data=None):
        super(F1ScoreCallback, self).__init__()
        self.validation_data = validation_data
        self.val_f1s = []
        
    def on_epoch_end(self, epoch, logs={}):
        if self.validation_data:
            val_predict = np.argmax(self.model.predict(self.validation_data[0]), axis=1)
            val_targ = self.validation_data[1]
            
            # Calculate F1 score - weighted average of all classes
            _val_f1 = f1_score(val_targ, val_predict, average='weighted')
            self.val_f1s.append(_val_f1)
            
            # Add to logs for TensorBoard or history tracking
            logs['val_f1'] = _val_f1
            
            print(f' - val_f1: {_val_f1:.4f}')

# Custom F1 Score metric function for model.compile
def f1_keras(y_true, y_pred):
    # Convert probabilities to class indices
    y_pred_classes = tf.argmax(y_pred, axis=1)
    y_true = tf.cast(y_true, tf.int64)
    
    # Calculate precision and recall
    true_positives = tf.cast(tf.math.count_nonzero(y_pred_classes * y_true), tf.float32)
    predicted_positives = tf.cast(tf.math.count_nonzero(y_pred_classes), tf.float32)
    actual_positives = tf.cast(tf.math.count_nonzero(y_true), tf.float32)
    
    precision = true_positives / (predicted_positives + tf.keras.backend.epsilon())
    recall = true_positives / (actual_positives + tf.keras.backend.epsilon())
    
    # Calculate F1 score
    f1 = 2 * precision * recall / (precision + recall + tf.keras.backend.epsilon())
    return f1



# Function to create and train LSTM model - updated for increased input features
def create_model(input_shape, num_classes):
    model = Sequential()
    model.add(Bidirectional(LSTM(256, activation='tanh', return_sequences=True), 
                          input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(128, activation='tanh'))
    model.add(Dropout(0.2))
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    
    model.compile(
        optimizer='adam', 
        loss='sparse_categorical_crossentropy', 
        metrics=['accuracy', f1_keras]
    )
    
    return model

# Main execution
if __name__ == "__main__":
    print("\nStep 1: Data Preparation")
    
    # File handling
    base_folder = "LSTM_Model"
    file_name = "M_and_D_sensors_labeled_AllSensors.json"
    file_path = os.path.join(base_folder, file_name)

    with open(file_path, 'r') as f:
        M_and_D_sensors_labeled_AllSensors = json.load(f)

    if not M_and_D_sensors_labeled_AllSensors:
        print("❌ Error: Data not loaded")
        exit(1)

    print("Creating dataset with extended time features...")
    X, y = create_dataset(M_and_D_sensors_labeled_AllSensors, time_steps=10)
    print(f"Dataset created with {len(X)} sequences")
    print(f"Feature vector size: {X.shape[1]} (includes start/end time features, duration, and sensor data)")
    print("saving data")
    save_dataset_to_file(X, y, "featureExtracted_AllSensors_ExtendedTimeFeatures.txt")
    print("data saved")
    
    # Display feature information
    sensor_count = 31 + 3  # M001-M031 + D001, D003, D004
    time_feature_count = 24 + 1  # 12 start features + 12 end features + 1 duration feature
    print(f"Sensor features: {sensor_count}")
    print(f"Time features: {time_feature_count}")
    print(f"Total features: {sensor_count + time_feature_count}")
    
    # Label encoding
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)
    print(f"Number of activity classes: {num_classes}")
    
    # Step 2: Cross-Validation Implementation
    print("\nStep 2: Implementing K-Fold Cross-Validation")
    
    n_splits = 10  # Number of folds
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # Metrics storage
    cv_accuracy = []
    cv_f1_scores = []
    cv_histories = []
    
    # For visualization
    plt.figure(figsize=(15, 15))
    
    fold = 1
    for train_index, test_index in kf.split(X,y_encoded):
        print(f"\n\n{'='*50}")
        print(f"Fold {fold}/{n_splits}")
        print(f"{'='*50}")
        
        # Split data
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y_encoded[train_index], y_encoded[test_index]
        
        # Standardize features - using only training data for fitting
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)  # Using the same scaler for test data
        
        # Split training data to create a validation set
        val_split_idx = int(len(X_train) * 0.9)
        X_val = X_train[val_split_idx:]
        y_val = y_train[val_split_idx:]
        X_train = X_train[:val_split_idx]
        y_train = y_train[:val_split_idx]
        
        # Reshape data for LSTM
        time_steps = 1
        X_train = X_train.reshape((X_train.shape[0], time_steps, X_train.shape[1]))
        X_val = X_val.reshape((X_val.shape[0], time_steps, X_val.shape[1]))
        X_test = X_test.reshape((X_test.shape[0], time_steps, X_test.shape[1]))
        
        # Create model
        model = create_model(input_shape=(X_train.shape[1], X_train.shape[2]), num_classes=num_classes)
        
        # Define callbacks
        f1_callback = F1ScoreCallback(validation_data=(X_val, y_val))
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.0001)
        
        # Train model
        print(f"\nTraining model for fold {fold}...")
        history = model.fit(
            X_train, y_train,
            epochs=50,  
            batch_size=32,
            validation_data=(X_val, y_val),
            callbacks=[f1_callback, early_stopping, reduce_lr],
            verbose=1
        )
        
        # Evaluate model
        print(f"\nEvaluating model for fold {fold}...")
        test_predictions = model.predict(X_test)
        predicted_classes = np.argmax(test_predictions, axis=1)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, predicted_classes)
        f1 = f1_score(y_test, predicted_classes, average='weighted')
        
        print(f"Fold {fold} - Accuracy: {accuracy:.4f}, F1 Score: {f1:.4f}")
        
        # Store metrics
        cv_accuracy.append(accuracy)
        cv_f1_scores.append(f1)
        cv_histories.append({
            'loss': history.history['loss'],
            'val_loss': history.history['val_loss'],
            'accuracy': history.history['accuracy'],
            'val_accuracy': history.history['val_accuracy'],
            'val_f1': f1_callback.val_f1s
        })
        
        # Plot training progress for this fold
        plt.subplot(n_splits, 3, (fold-1)*3 + 1)
        plt.plot(history.history['loss'], label='Train Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title(f"Fold {fold} - Loss")
        plt.legend()
        
        plt.subplot(n_splits, 3, (fold-1)*3 + 2)
        plt.plot(history.history['accuracy'], label='Train Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.title(f"Fold {fold} - Accuracy")
        plt.legend()
        
        plt.subplot(n_splits, 3, (fold-1)*3 + 3)
        plt.plot(f1_callback.val_f1s, label='Validation F1 Score')
        plt.title(f"Fold {fold} - F1 Score")
        plt.legend()
        
        # Print classification report for this fold
        print("\nClassification Report for fold {}:".format(fold))
        print(classification_report(
        y_test,
        predicted_classes,
        target_names=label_encoder.classes_,
        zero_division=0  # Added parameter
        ))
        
        # Save model and scaler for this fold
        model.save(f"lstm_activity_classifier_fold{fold}_with_extended_time.keras")
        with open(f'feature_scaler_fold{fold}_with_extended_time.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        
        # Increment fold counter
        fold += 1
    
    # Finalize and display overall cross-validation results
    plt.tight_layout()
    plt.savefig('cross_validation_results_with_extended_time_features.png')
    plt.show()
    
    # Plot feature importance
    # Get the weights of the first layer
    last_model = model  # Using the last trained model
    
    # Get the weights of the first layer
    first_layer_weights = np.abs(last_model.layers[0].get_weights()[0]).mean(axis=( 1))
    
    # Create feature names for visualization
    feature_names = []
    
    # Start time features
    for prefix in ["start_", "end_"]:
        for component in ["hour", "minute", "day", "month", "day_of_week", "time_of_day"]:
            for encoding in ["sin", "cos"]:
                feature_names.append(f"{prefix}{component}_{encoding}")
    
    # Duration feature
    feature_names.append("activity_duration_normalized")
    
    # Sensor features
    for i in range(1, 32):
        feature_names.append(f"M{i:03d}")
    feature_names.extend(["D001", "D003", "D004"])
    
    # Sort features by importance
    indices = np.argsort(first_layer_weights)[::-1]
    plt.figure(figsize=(12, 8))
    plt.bar(range(len(indices)), first_layer_weights[indices])
    plt.xticks(range(len(indices)), [feature_names[i] for i in indices], rotation=90)
    plt.title('Approximate Feature Importance based on Layer Weights')
    plt.tight_layout()
    plt.savefig('feature_importance_with_extended_time.png')
    
    # Print average metrics
    print("\n\n" + "="*50)
    print("CROSS-VALIDATION RESULTS")
    print("="*50)
    print(f"Number of folds: {n_splits}")
    print(f"Average Accuracy: {np.mean(cv_accuracy):.4f} ± {np.std(cv_accuracy):.4f}")
    print(f"Average F1 Score: {np.mean(cv_f1_scores):.4f} ± {np.std(cv_f1_scores):.4f}")
    
    # Save label encoder classes for future use
    np.save('activity_classes.npy', label_encoder.classes_)
    print("\nActivity classes saved as 'activity_classes.npy'")
    
    print("\nCross-validation complete!")
