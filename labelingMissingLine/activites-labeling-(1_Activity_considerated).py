import json
import datetime
from copy import deepcopy
import os
base_folder = "labelingMissingLine"

# ======================================================
# MAIN PURPOSE:
# This script labels unlabeled activity sequences in a timeline of events.
# it considerate the sequnce between the end of an activity and the
# beginning of another as one activity
# It uses patterns of preceding/following activities, time of day,
# and sensor activations to intelligently infer activities.
# ======================================================

def parse_time(time_str):
    """Parse time string to hours and minutes."""
    hours, minutes = map(int, time_str.split(':')[:2])
    return hours, minutes

def get_time_zone(time_str):
    """
    Determine if a time is morning, afternoon, or night.
    
    Parameters:
        time_str (str): Time string in format 'HH:MM:SS'
    
    Returns:
        str: Time zone label - "morning" (5:00-11:59), "afternoon" (12:00-17:59), 
             or "night" (18:00-4:59)
    """
    hours = int(time_str.split(':')[0])
    if 5 <= hours < 12:
        return "morning"
    elif 12 <= hours < 18:
        return "afternoon"
    else:
        return "night"

def find_closest_time(target_time, available_times):
    """
    Find the closest time from a list of available times.
    Handles midnight crossing (e.g., 23:00 is closer to 01:00 than to 12:00).
    
    Parameters:
        target_time (str): Time to find closest match for in 'HH:MM' format
        available_times (list): List of time strings to compare against
    
    Returns:
        str: The closest matching time from available_times
    """
    target_h, target_m = parse_time(target_time)
    target_minutes = target_h * 60 + target_m
    
    closest_time = None
    min_diff = float('inf')
    
    for time_str in available_times:
        h, m = parse_time(time_str)
        minutes = h * 60 + m
        diff = abs(minutes - target_minutes)
        
        # Handle midnight crossing
        if diff > 720:  # 12 hours in minutes
            diff = 1440 - diff  # 24 hours in minutes
            
        if diff < min_diff:
            min_diff = diff
            closest_time = time_str
            
    return closest_time

def calculate_sensor_score(sensor_data, activity, active_sensors):
    """
    Calculate a score for how well active sensors match an activity's typical sensors.
    
    Parameters:
        sensor_data (dict): Dictionary mapping activities to their typical sensors
        activity (str): The activity to calculate score for
        active_sensors (list): List of sensors active during the sequence
    
    Returns:
        float: Score representing how well the active sensors match the activity
               Higher scores mean better match
    """
    if activity not in sensor_data:
        return 0
    
    activity_sensors = sensor_data[activity]
    
    # Convert occurrences to integers for weighting
    sensor_weights = {
        sensor_id: int(sensor_info["occurrence"]) 
        for sensor_id, sensor_info in activity_sensors.items()
    }
    
    # Calculate total weight of all sensors for this activity
    total_weight = sum(sensor_weights.values())
    
    # Calculate the sum of weights for active sensors that match this activity
    matching_weight = sum(
        sensor_weights.get(sensor, 0) for sensor in active_sensors
    )
    
    # Prevent division by zero
    if total_weight == 0:
        return 0
    
    # Score is the percentage of total sensor weight that matches active sensors
    return matching_weight / total_weight

def get_active_sensors(data, start_idx, end_idx):
    """
    Extract the list of active sensors during a sequence.
    
    Parameters:
        data (list): The event data
        start_idx (int): Start index of the sequence
        end_idx (int): End index of the sequence
    
    Returns:
        list: List of active sensor IDs during the sequence
    """
    active_sensors = set()
    
    for i in range(start_idx, end_idx + 1):
        if 'sensor' in data[i] and data[i]['sensor'] is not None:
            active_sensors.add(data[i]['sensor'])
    
    return list(active_sensors)

def label_activities(data, precedent_following, zone_time_data, sensor_data):
    """
    Label unlabeled sequences in the data by inferring activities.
    
    Algorithm:
    1. Identify activity boundary markers (begin/end)
    2. Find unlabeled sequences between end->begin markers
    3. For each unlabeled sequence:
       a. Determine what activities could occur between the preceding and following activities
       b. Check what time of day it is (morning/afternoon/night)
       c. Analyze which sensors were active during the sequence
       d. Choose the most probable activity based on timing patterns and sensor activations
    
    Parameters:
        data (list): List of event dictionaries with 'time' and 'activity' fields
        precedent_following (list): Rules for which activities typically follow others
        zone_time_data (dict): Data about when activities typically occur by time zone
        sensor_data (dict): Mapping of activities to their typical sensors
    
    Returns:
        list: Copy of input data with labels added to previously unlabeled events
    """
    labeled_data = deepcopy(data)
    
    # Find activity boundaries (begin/end)
    activity_markers = []
    for i, event in enumerate(data):
        if event['activity'] is not None:
            if ',begin' in event['activity'] or ',end' in event['activity']:
                activity_markers.append((i, event['activity']))
    
    # Identify unlabeled sequences (gaps between an activity end and next activity begin)
    unlabeled_sequences = []
    for i in range(len(activity_markers) - 1):
        current_idx, current_desc = activity_markers[i]
        next_idx, next_desc = activity_markers[i + 1]
        
        # If current is an end and next is a begin, we have an unlabeled sequence
        if ',end' in current_desc and ',begin' in next_desc:
            unlabeled_sequences.append((current_idx + 1, next_idx - 1, current_desc, next_desc))
    
    # Process each unlabeled sequence
    for start_idx, end_idx, prev_desc, next_desc in unlabeled_sequences:
        if start_idx > end_idx:
            continue  # Skip empty sequences
            
        # Extract previous and next activities
        prev_activity = prev_desc.split(',')[0]
        next_activity = next_desc.split(',')[0]
        
        # Get time zone of the sequence (morning/afternoon/night)
        sequence_time = data[start_idx]['time'].split('.')[0]  # Remove milliseconds
        time_zone = get_time_zone(sequence_time)
        
        # Get active sensors during this sequence
        active_sensors = get_active_sensors(data, start_idx, end_idx)
        
        # Find possible activities based on precedent and following relationships
        possible_activities = []
        for activity_info in precedent_following:
            activity = activity_info['activity']
            precedents = activity_info['precedentActivities']
            followings = activity_info['followingActivities']
            
            # Check if this activity could occur between prev_activity and next_activity
            if prev_activity in precedents and next_activity in followings:
                possible_activities.append(activity)
        
        # If no activities match the pattern, consider all activities as possibilities
        if not possible_activities:
            possible_activities = [info['activity'] for info in precedent_following]
        
        # Find the most probable activity based on time zone and sensors
        best_activity = None
        best_score = float('-inf')
        
        for activity in possible_activities:
            # Calculate time-based score (lower time difference is better)
            time_score = 0
            if activity in zone_time_data:
                activity_time_data = zone_time_data[activity]
                if time_zone in activity_time_data['average_start_time']:
                    avg_start_time = activity_time_data['average_start_time'][time_zone]
                    
                    # Extract just HH:MM from sequence time
                    sequence_hour, sequence_minute = sequence_time.split(':')[:2]
                    sequence_time_str = f"{sequence_hour}:{sequence_minute}"
                    
                    # Calculate time difference in minutes
                    seq_h, seq_m = parse_time(sequence_time_str)
                    avg_h, avg_m = parse_time(avg_start_time)
                    
                    seq_minutes = seq_h * 60 + seq_m
                    avg_minutes = avg_h * 60 + avg_m
                    
                    time_diff = abs(seq_minutes - avg_minutes)
                    # Handle midnight crossing
                    if time_diff > 720:  # 12 hours in minutes
                        time_diff = 1440 - time_diff  # 24 hours in minutes
                    
                    # Convert time difference to a score (lower difference = higher score)
                    # Max difference is 720 minutes (12 hours), so normalize to 0-1 range
                    time_score = 1 - (time_diff / 720)
            
            # Calculate sensor-based score
            sensor_score = calculate_sensor_score(sensor_data, activity, active_sensors)
            
            # Combine scores (weighted average)
            # Give more weight to sensor data if available
            if active_sensors:
                combined_score = (time_score * 0.4) + (sensor_score * 0.6)
            else:
                combined_score = time_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_activity = activity
        
        # If no best activity found, use fallbacks
        if best_activity is None and possible_activities:
            best_activity = possible_activities[0]
        elif best_activity is None:
            best_activity = "Unknown_Activity"
        
        # Label the first and last events in the sequence
        labeled_data[start_idx]['activity'] = f"{best_activity},begin"
        labeled_data[end_idx]['activity'] = f"{best_activity},end"
    
    return labeled_data

def main():
    """
    Main function that orchestrates the activity labeling process:
    1. Load test data, precedent/following rules, time zone data, and sensor data
    2. Perform activity labeling
    3. Save the labeled output
    """
    # Load the test data
    file_name = "M_and_D_sensors.json"
    file_path = os.path.join(base_folder, file_name)
    with open(file_path, 'r') as f:
        test_data = json.load(f)
    
    # Load precedent and following activities
    file_name = 'Following&PrecedentActivitiesForEachActivities.json'
    file_path = os.path.join(base_folder, file_name)
    with open(file_path, 'r') as f:
        precedent_following = json.load(f)
    
    # Load zone time data
    file_name = 'zoneTimeForEachActivity.json'
    file_path = os.path.join(base_folder, file_name)
    with open(file_path, 'r') as f:
        zone_time_data = json.load(f)
    
    # Load sensor data for activities
    file_name = 'pertinentsSonsorsForEachActivity.json'
    file_path = os.path.join(base_folder, file_name)
    with open(file_path, 'r') as f:
        sensor_data = json.load(f)
    
    # Label activities
    labeled_data = label_activities(test_data, precedent_following, zone_time_data, sensor_data)
    
    # Save the labeled data
    with open('M_and_D_sensors_labeled_SensorsIntegration.json', 'w') as f:
        json.dump(labeled_data, f, indent=4)
    
    print("Activity labeling completed. Output saved to M_and_D_sensors_labeled.json")

if __name__ == "__main__":
    main()
