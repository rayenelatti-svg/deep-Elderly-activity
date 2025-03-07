import json
from copy import deepcopy
import os

base_folder = "labelingMissingLine"

def create_sensor_to_location_map(sensors_location):
    sensor_to_location = {}
    for location, info in sensors_location[0].items():
        for sensor in info['sensors']:
            sensor_to_location[sensor] = location
    return sensor_to_location

def get_activity_locations(sensor_data):
    activity_locations = {}
    for activity, sensors in sensor_data.items():
        locations = set(sensor_info["localization"] for sensor_info in sensors.values())
        activity_locations[activity] = locations
    return activity_locations

def get_active_sensors_and_locations(data, start_idx, end_idx, sensor_to_location):
    active_sensors = set()
    for i in range(start_idx, end_idx + 1):
        if data[i].get('sensor'):
            active_sensors.add(data[i]['sensor'])
    locations = {sensor_to_location[s] for s in active_sensors if s in sensor_to_location}
    return list(active_sensors), locations

def determine_activity_by_location_priority(active_sensors, active_locations, sensor_data, activity_locations):
    candidates = []
    location_matched = [act for act, locs in activity_locations.items() 
                       if any(l in active_locations for l in locs)]
    
    if not location_matched:
        location_matched = list(sensor_data.keys())
    
    for activity in location_matched:
        act_sensors = sensor_data[activity]
        match_count = sum(1 for s in active_sensors if s in act_sensors)
        occurrence = sum(int(act_sensors[s]["occurrence"]) for s in active_sensors if s in act_sensors)
        loc_ratio = len(active_locations & activity_locations[activity]) / max(len(active_locations), 1)
        score = (loc_ratio * 0.7) + (match_count/len(active_sensors) * 0.3 if active_sensors else 0)
        candidates.append((activity, score, occurrence))
    
    candidates.sort(key=lambda x: (-x[1], -x[2]))
    return candidates[0][0] if candidates else "Unknown_Activity"

def label_gaps_between_activities(data, sensors_location, sensor_data):
    labeled_data = deepcopy(data)
    sensor_to_location = create_sensor_to_location_map(sensors_location)
    activity_locations = get_activity_locations(sensor_data)
    
    # Get all pertinent sensors across all activities
    all_pertinent_sensors = set()
    for activity_sensors in sensor_data.values():
        all_pertinent_sensors.update(activity_sensors.keys())
    
    # Find activity markers and gaps
    activity_markers = [(i, e['activity']) for i, e in enumerate(data) 
                       if e.get('activity') and ('begin' in e['activity'] or 'end' in e['activity'])]
    
    unlabeled_gaps = [(activity_markers[i][0]+1, activity_markers[i+1][0]-1)
                     for i in range(len(activity_markers)-1)
                     if 'end' in activity_markers[i][1] and 'begin' in activity_markers[i+1][1]
                     and activity_markers[i][0]+1 <= activity_markers[i+1][0]-1]
    
    for gap_start, gap_end in unlabeled_gaps:
        current_start = gap_start
        prev_locations = set()
        
        for i in range(gap_start, gap_end+1):
            curr_sensors, curr_locs = get_active_sensors_and_locations(data, i, i, sensor_to_location)
            
            if i == gap_start:
                prev_locations = curr_locs
                continue
            
            # Detect location changes
            location_change = bool(curr_locs - prev_locations) or bool(prev_locations - curr_locs)
            
            if location_change and curr_sensors:
                # Process previous interval
                sub_sensors, sub_locs = get_active_sensors_and_locations(
                    data, current_start, i-1, sensor_to_location
                )
                
                if sub_sensors:
                    # Check for non-pertinent sensors
                    if all(s not in all_pertinent_sensors for s in sub_sensors):
                        activity = "Other"
                    else:
                        activity = determine_activity_by_location_priority(
                            sub_sensors, sub_locs, sensor_data, activity_locations
                        )
                    
                    # Apply labels
                    if activity == "Other":
                        labeled_data[current_start]['activity'] = "Other"
                        labeled_data[i-1]['activity'] = "Other"
                    else:
                        labeled_data[current_start]['activity'] = f"{activity},begin,modified"
                        labeled_data[i-1]['activity'] = f"{activity},end,modified"
                
                current_start = i
            prev_locations = curr_locs.copy()
        
        # Process remaining interval
        sub_sensors, sub_locs = get_active_sensors_and_locations(
            data, current_start, gap_end, sensor_to_location
        )
        if sub_sensors:
            if all(s not in all_pertinent_sensors for s in sub_sensors):
                activity = "Other"
            else:
                activity = determine_activity_by_location_priority(
                    sub_sensors, sub_locs, sensor_data, activity_locations
                )
            
            if activity == "Other":
                labeled_data[current_start]['activity'] = "Other"
                labeled_data[gap_end]['activity'] = "Other"
            else:
                labeled_data[current_start]['activity'] = f"{activity},begin,modified"
                labeled_data[gap_end]['activity'] = f"{activity},end,modified"
    
    return labeled_data

def main():
    # Load data files
    input_files = [
        "M_and_D_sensors.json",
        "sonsorsLocalisation.json",
        "AllSensorsForEachActivities.json"
    ]
    
    loaded_data = []
    for file in input_files:
        with open(os.path.join(base_folder, file), 'r') as f:
            loaded_data.append(json.load(f))
    
    test_data, sensors_loc, sensor_data = loaded_data
    
    # Process labeling
    labeled_data = label_gaps_between_activities(test_data, sensors_loc, sensor_data)
    
    # Save output
    output_file = "M_and_D_sensors_labeled_(AllSensors)(indexedByModified).json"
    with open(output_file, 'w') as f:
        json.dump(labeled_data, f, indent=4)
    
    print(f"Labeling complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()