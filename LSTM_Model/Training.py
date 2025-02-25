# Import required libraries
import numpy as np  # Numerical computing library for array operations
import matplotlib.pyplot as plt  # Plotting library for visualization
from tensorflow.keras.models import Sequential  # Keras model class for building neural networks
from tensorflow.keras.layers import LSTM, Dense  # LSTM and Dense layer implementations
from sklearn.metrics import mean_absolute_error  # Metric for model evaluation

import os
import json
import glob

import os
import json

# Liste des fichiers JSON à charger
json_file_names = [
    "ActivitiesForEachPerminentSensor.json",
    "avgDurationForEachActivities.json",
    "avgEventCountForEachActivity.json",
    "Following&PrecedentActivitiesForEachActivities.json",
    "M_and_D_sensors_filtered.json",
    "M_and_D_sensors.json",
    "pertinentsSonsorsForEachActivity.json", 
    "sonsorsLocalisation.json",
    "zoneTimeForEachActivity.json"
]

# Chemin correct vers les fichiers
base_folder = "LSTM_Model"  # Sans le préfixe DEEP-ELDERLY...

# Charger les données
data = {}
for file_name in json_file_names:
    file_path = os.path.join(base_folder, file_name)
    try:
        if not os.path.exists(file_path):
            print(f"❌ Erreur: {file_path} n'existe pas.")
            continue
        
        with open(file_path, "r", encoding="utf-8") as file:
            data[file_name] = json.load(file)
            

        print(f"✅ {file_name} chargé avec succès")
    
    except json.JSONDecodeError:
        print(f"❌ Erreur: {file_name} contient du JSON invalide.")
    except Exception as e:
        print(f"❌ Erreur inattendue avec {file_name}: {e}")

# Affectation à des variables séparées
ActivitiesForEachPermanentSensor = data.get("ActivitiesForEachPerminentSensor.json")
avgDurationForEachActivities = data.get("avgDurationForEachActivities.json")
Following_PrecedentActivitiesForEachActivities = data.get("Following&PrecedentActivitiesForEachActivities.json")
M_and_D_sensors_filtered = data.get("M_and_D_sensors_filtered.json")
M_and_D_sensors = data.get("M_and_D_sensors.json")
pertinentsSensorsForEachActivity = data.get("pertinentsSensorsForEachActivity.json")
sonsorsLocalisation = data.get("sonsorsLocalisation.json")  # Note: faute de frappe probable

zoneTimeForEachActivity = data.get("zoneTimeForEachActivity.json")

import numpy as np
from datetime import datetime



def create_dataset(data, time_steps=8):
    """
    Create dataset handling overlapping activities with robust error handling
    """
    X, y = [], []
    all_sensors = [f"M{i:03d}" for i in range(1, 32)] + ["D001", "D003", "D004"]
    
    # Keep track of active activities across all sequences
    global_active_activities = {}
    
    for i in range(len(data) - time_steps):
        sequence = data[i:i + time_steps]
        
        # Dictionary to track line counts for each activity in this sequence
        activity_line_counts = {}
        
        # Copy the active activities from previous sequence
        active_activities = global_active_activities.copy()
        
        # 1. First pass: Track begin/end markers
        for j, event in enumerate(sequence):
            if event["activity"]:
                # Clean up the activity string and split
                activity_parts = event["activity"].replace(" ", "").split(",")
                if len(activity_parts) != 2:
                    continue  # Skip malformed activity entries
                    
                activity_name, action = activity_parts
                
                if action == "begin":
                    active_activities[activity_name] = j  # Store start index
                elif action == "end":
                    if activity_name in active_activities:
                        start_idx = active_activities[activity_name]
                        # Count lines between begin and end
                        activity_line_counts[activity_name] = activity_line_counts.get(activity_name, 0) + (j - start_idx + 1)
                        active_activities.pop(activity_name, None)  # Safely remove the activity
                    else:
                        # If we find an end without a begin, assume it started at the beginning of the sequence
                        activity_line_counts[activity_name] = activity_line_counts.get(activity_name, 0) + (j + 1)
        
        # 2. Second pass: Count lines for activities that don't end in this sequence
        for activity, start_idx in active_activities.items():
            if activity not in activity_line_counts:
                # Count from start to end of sequence
                activity_line_counts[activity] = time_steps - start_idx
        
        # Update global tracking for next sequence
        global_active_activities = active_activities
        
        # 3. Process sensor data for X
        start_dt = datetime.strptime(f"{sequence[0]['date']} {sequence[0]['time']}", "%Y-%m-%d %H:%M:%S.%f")
        end_dt = datetime.strptime(f"{sequence[-1]['date']} {sequence[-1]['time']}", "%Y-%m-%d %H:%M:%S.%f")
        duration = (end_dt - start_dt).total_seconds()
        
        sensor_counts = {sensor: 0 for sensor in all_sensors}
        X_sequence = []
        
        for event in sequence:
            if event["state"] == "ON" and event["sensor"] in sensor_counts:
                sensor_counts[event["sensor"]] += 1
            
            feature_row = [
                start_dt.timestamp(),
                end_dt.timestamp(),
                duration
            ] + [sensor_counts[sensor] for sensor in all_sensors]
            
            X_sequence.append(feature_row)
        
        X.append(X_sequence)
        
        # 4. Determine majority activity for y
        if activity_line_counts:
            majority_activity = max(activity_line_counts.items(), key=lambda x: x[1])[0]
        else:
            # If no activities found in this sequence, check global tracking
            if global_active_activities:
                majority_activity = list(global_active_activities.keys())[0]
            else:
                majority_activity = "None"
                
        y.append(majority_activity)
    
    return np.array(X, dtype=np.float32), np.array(y)

# ---------------------------------------------------
# Exemple d'utilisation
# ---------------------------------------------------




def save_dataset_to_file(X, y, filename="dataset_output.txt"):
    with open(filename, 'w') as f:
        for i in range(len(X)):
            f.write(f"X[{i}]:\n")
            # Write each timestep on a new line with some indentation
            for timestep in X[i]:
                f.write(f"    {timestep.tolist()}\n")
            f.write(f"y[{i}]: {y[i]}\n")
            f.write("_" * 50 + "\n\n")  # Add separator line

# Use the function
X, y = create_dataset(M_and_D_sensors_filtered)
save_dataset_to_file(X,y)

print("Dataset has been saved to dataset_output.txt")

