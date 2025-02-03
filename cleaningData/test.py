import json
from collections import defaultdict
import time

def analyze_sensor_activities(data):
    start_time = time.time()
    
    # Remove duplicates
    print("Removing duplicates...")
    unique_data = []
    seen = set()
    for item in data:
        key = (item['date'], item['time'], item['sensor'], item['state'], item['description'])
        if key not in seen:
            unique_data.append(item)
            seen.add(key)
    print(f"Removed duplicates. Unique entries count: {len(unique_data)}")
    
    # Track activities
    print("Tracking activities...")
    activities = {}
    activities_found = set(item['description'].split(',')[0] for item in unique_data if item.get('description') and item['description'].endswith(',begin'))
    print(f"Found activities: {activities_found}")

    for activity in activities_found:
        print(f"Processing activity: {activity}")
        # Initialize activity entry
        activities[activity] = {}
        
        # Find all begin-end couples for this activity
        begin_entries = [e for e in unique_data if e.get('description') == f'{activity},begin']
        end_entries = [e for e in unique_data if e.get('description') == f'{activity},end']
        print(f"Found {len(begin_entries)} begin entries and {len(end_entries)} end entries for activity: {activity}")

        # Track total sensor occurrences for this activity
        total_sensor_occurrences = defaultdict(int)
        
        # Process each begin-end couple
        for i, (begin_entry, end_entry) in enumerate(zip(begin_entries, end_entries), 1):
            print(f"Processing begin-end pair {i} for activity: {activity}")
            # Find sensors between begin and end
            sensors = defaultdict(int)
            for item in unique_data:
                if (begin_entry['date'] == item['date'] and 
                    begin_entry['time'] <= item['time'] <= end_entry['time'] and
                    item['sensor'] not in [begin_entry['sensor'], end_entry['sensor']]):
                    sensors[item['sensor']] += 1
                    total_sensor_occurrences[item['sensor']] += 1
            
            # Create an entry for this begin-end couple
            if i == 1:
                activities[activity]['begin date'] = f"{begin_entry['date']} {begin_entry['time']}"
                activities[activity]['end date'] = f"{end_entry['date']} {end_entry['time']}"
                activities[activity]['sensors'] = dict(sensors)
            else:
                activities[activity][f'begin date {i}'] = f"{begin_entry['date']} {begin_entry['time']}"
                activities[activity][f'end date {i}'] = f"{end_entry['date']} {end_entry['time']}"
                activities[activity][f'sensors {i}'] = dict(sensors)
        
        # Add total sensor occurrences
        activities[activity]['total_sensor_occurrences'] = dict(total_sensor_occurrences)
        print(f"Finished processing activity: {activity}")

    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    return {'activity_sensor_occurrences': activities}

# Process data and write to file
print("Loading data from M&D_sensors.json...")
with open('M&D_sensors.json', 'r') as file:
    data = json.load(file)
print(f"Loaded {len(data)} entries from M&D_sensors.json.")

result = analyze_sensor_activities(data)

print("Writing results to sensorForEachActivity.json...")
with open('sensorForEachActivity.json', 'w') as outfile:
    json.dump(result, outfile, indent=2)
print("Results saved to sensorForEachActivity.json")