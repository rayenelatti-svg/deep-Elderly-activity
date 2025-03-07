
"""
Create_LSTM_Input.py

This file focuses on preparing time-series data for LSTM-based activity recognition. Its main functions:

1. encode_cyclical_feature(): Encodes cyclical features (like hours, days, months) using sine and cosine
   transformations to preserve their periodicity.

2. extract_time_features(): Extracts temporal features from datetime objects, encoding them as cyclical 
   components with sin/cos values to capture time patterns.

3. create_dataset(): The core function that processes sensor event data to create feature vectors for LSTM.
   It tracks activity start/end times, calculates durations, extracts time features, and counts sensor
   activations to build a comprehensive feature set.

4. save_dataset_to_file(): Outputs the generated dataset to a text file with labeled features for inspection.

The file handles complex event sequences by tracking overlapping activities, determining majority activities
in time windows, and encoding time data in a way that preserves cyclical relationships.
"""

import numpy as np
from datetime import datetime, timedelta

# Time feature encoding functions
def encode_cyclical_feature(value, period):
    """
    Encode a cyclical feature using sin and cos transformation to preserve periodicity.
    For example: hour of day (period=24), day of week (period=7), month (period=12)
    
    Args:
        value: The value to encode
        period: The period of the feature
        
    Returns:
        sin_component, cos_component as a tuple
    """
    sin_component = np.sin(2 * np.pi * value / period)
    cos_component = np.cos(2 * np.pi * value / period)
    return sin_component, cos_component

def extract_time_features(dt, prefix=""):
    """
    Extract and encode cyclical time features from a datetime object
    
    Args:
        dt: datetime object
        prefix: optional prefix for feature keys (e.g., "start_" or "end_")
        
    Returns:
        Dictionary of encoded time features
    """
    if dt is None:
        # Return zeros if no datetime is provided
        return {
            f'{prefix}hour_sin': 0,
            f'{prefix}hour_cos': 0,
            f'{prefix}minute_sin': 0,
            f'{prefix}minute_cos': 0,
            f'{prefix}second_sin': 0,
            f'{prefix}second_cos': 0,
            f'{prefix}day_sin': 0,
            f'{prefix}day_cos': 0,
            f'{prefix}month_sin': 0,
            f'{prefix}month_cos': 0,
            f'{prefix}day_of_week_sin': 0,
            f'{prefix}day_of_week_cos': 0,
            f'{prefix}time_of_day_sin': 0,
            f'{prefix}time_of_day_cos': 0
        }
    
    # Extract basic time components
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    day = dt.day
    month = dt.month
    day_of_week = dt.weekday()  # 0-6 (Monday to Sunday)
    
    # Calculate total time in seconds for the day (0-86399)
    time_of_day = hour * 3600 + minute * 60 + second
    
    # Encode cyclical features
    hour_sin, hour_cos = encode_cyclical_feature(hour, 24)
    minute_sin, minute_cos = encode_cyclical_feature(minute, 60)
    second_sin, second_cos = encode_cyclical_feature(second, 60)
    day_sin, day_cos = encode_cyclical_feature(day, 31)  # Using 31 as max days in month
    month_sin, month_cos = encode_cyclical_feature(month, 12)
    day_of_week_sin, day_of_week_cos = encode_cyclical_feature(day_of_week, 7)
    time_of_day_sin, time_of_day_cos = encode_cyclical_feature(time_of_day, 86400)
    
    # Return encoded features with optional prefix
    return {
        f'{prefix}hour_sin': hour_sin,
        f'{prefix}hour_cos': hour_cos,
        f'{prefix}minute_sin': minute_sin,
        f'{prefix}minute_cos': minute_cos,
        f'{prefix}second_sin': second_sin,
        f'{prefix}second_cos': second_cos,
        f'{prefix}day_sin': day_sin,
        f'{prefix}day_cos': day_cos,
        f'{prefix}month_sin': month_sin,
        f'{prefix}month_cos': month_cos,
        f'{prefix}day_of_week_sin': day_of_week_sin,
        f'{prefix}day_of_week_cos': day_of_week_cos,
        f'{prefix}time_of_day_sin': time_of_day_sin,
        f'{prefix}time_of_day_cos': time_of_day_cos
    }

# Updated create_dataset function with start/end times and duration
def create_dataset(data, time_steps=10):
    X, y = [], []
    all_sensors = [f"M{i:03d}" for i in range(1, 32)] + ["D001", "D003", "D004"]
    
    # Stocke les activités actives avec leur temps de début (datetime) et position de départ
    global_active_activities = {}  # Format: {activity: (start_idx, start_dt)}
    last_majority_activity = None

    # Définition des noms de caractéristiques temporelles
    start_time_feature_names = [
        'start_hour_sin', 'start_hour_cos', 'start_minute_sin', 'start_minute_cos',
        'start_day_sin', 'start_day_cos', 'start_month_sin', 'start_month_cos',
        'start_day_of_week_sin', 'start_day_of_week_cos'
    ]
    end_time_feature_names = [
        'end_hour_sin', 'end_hour_cos', 'end_minute_sin', 'end_minute_cos',
        'end_day_sin', 'end_day_cos', 'end_month_sin', 'end_month_cos',
        'end_day_of_week_sin', 'end_day_of_week_cos'
    ]

    for i in range(0, len(data) - time_steps + 1, time_steps):
        sequence = data[i:i + time_steps]
        activity_line_counts = {}
        
        # Copie les activités globales avec leur historique complet
        active_activities = global_active_activities.copy()
        activity_durations = {}

        # Traitement des événements de la séquence
        for j, event in enumerate(sequence):
            if event["activity"]:
                activity_parts = event["activity"].replace(" ", "").split(",")
                if len(activity_parts) != 2: continue
                activity_name, action = activity_parts

                # Parsing du datetime
                try:
                    event_dt = datetime.strptime(
                        f"{event['date']} {event['time']}", 
                        "%Y-%m-%d %H:%M:%S.%f"
                    )
                except ValueError:
                    try:
                        event_dt = datetime.strptime(
                            f"{event['date']} {event['time']}", 
                            "%Y-%m-%d %H:%M:%S"
                        )
                    except:
                        event_dt = datetime.now()

                # Logique begin/end
                if action == "begin":
                    active_activities[activity_name] = (j, event_dt)
                elif action == "end":
                    if activity_name in active_activities:
                        start_idx, start_dt = active_activities[activity_name]
                        duration_sec = (event_dt - start_dt).total_seconds()
                        activity_durations[activity_name] = duration_sec
                        del active_activities[activity_name]

        # Gestion des activités non terminées
        for activity, (start_idx, start_dt) in active_activities.items():
            last_event_dt = datetime.strptime(
                f"{sequence[-1]['date']} {sequence[-1]['time']}", 
                "%Y-%m-%d %H:%M:%S.%f"
            ) if sequence else datetime.now()
            duration_sec = (last_event_dt - start_dt).total_seconds()
            activity_durations[activity] = duration_sec

        # Mise à jour des activités globales
        global_active_activities = active_activities.copy()

        # Détermination de l'activité majoritaire
        if activity_durations:
            majority_activity = max(activity_durations.items(), key=lambda x: x[1])[0]
        else:
            majority_activity = last_majority_activity or "None"
        
        if majority_activity == "None" and last_majority_activity:
            majority_activity = last_majority_activity
        last_majority_activity = majority_activity

        # Extraction des caractéristiques temporelles
        start_dt = active_activities.get(majority_activity, (0, None))[1]
        end_dt = start_dt + timedelta(seconds=activity_durations.get(majority_activity, 0)) if start_dt else None

        start_features = extract_time_features(start_dt, "start_")
        end_features = extract_time_features(end_dt, "end_")
        
        # Normalisation de la durée
        duration_norm = activity_durations.get(majority_activity, 0) / 86400
        duration_norm = max(duration_norm, 0.0001)  # Évite les valeurs nulles

        # Comptage des capteurs
        sensor_counts = [sum(1 for e in sequence if e["sensor"] == s and e["state"] == "ON") for s in all_sensors]

        # Création du vecteur de caractéristiques
        feature_vector = (
            [start_features[name] for name in start_time_feature_names] +
            [end_features[name] for name in end_time_feature_names] +
            [duration_norm] +
            sensor_counts
        )
        
        X.append(feature_vector)
        y.append(majority_activity)

    return np.array(X, dtype=np.float32), np.array(y)


def save_dataset_to_file(X, y, filename="dataset_output.txt"):
    """
    Save the dataset to a readable text file, with named features for easy inspection.
    """
    # Build the correct list of feature names based on create_dataset output
    feature_names = []
    
    # Time features for start (10 features)
    start_features = [
        'start_hour_sin', 'start_hour_cos', 
        'start_minute_sin', 'start_minute_cos', 
        'start_day_sin', 'start_day_cos', 
        'start_month_sin', 'start_month_cos', 
        'start_day_of_week_sin', 'start_day_of_week_cos'
    ]
    # Time features for end (10 features)
    end_features = [
        'end_hour_sin', 'end_hour_cos', 
        'end_minute_sin', 'end_minute_cos', 
        'end_day_sin', 'end_day_cos', 
        'end_month_sin', 'end_month_cos', 
        'end_day_of_week_sin', 'end_day_of_week_cos'
    ]
    feature_names.extend(start_features)
    feature_names.extend(end_features)
    
    # Duration feature (1 feature)
    feature_names.append("activity_duration_normalized")
    
    # Sensor features (34 features)
    for i in range(1, 32):
        feature_names.append(f"M{i:03d}")
    feature_names.extend(["D001", "D003", "D004"])
    
    with open(filename, 'w') as f:
        for i in range(len(X)):
            f.write(f"X[{i}]: [\n")
            
            # Write time features (20 features)
            f.write("    # Time Features (20 features: 10 for start date, 10 for end date)\n")
            for j in range(20):
                f.write(f"    '{feature_names[j]}': {X[i][j]},\n")
            
            # Write duration feature
            duration_idx = 20
            f.write(f"    '{feature_names[duration_idx]}': {X[i][duration_idx]},  # Normalized activity duration\n")
            
            # Write sensor features (remaining 34 features)
            f.write("    # Sensor Features (34 features)\n")
            for j in range(duration_idx + 1, len(feature_names)):
                f.write(f"    '{feature_names[j]}': {X[i][j]}")
                if j < len(feature_names) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")
            
            f.write("]\n")
            f.write(f"y[{i}]: '{y[i]}'\n")
            f.write("_" * 50 + "\n\n")