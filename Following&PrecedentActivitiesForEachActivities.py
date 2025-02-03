import json
from datetime import datetime

def load_sensor_data(file_path):
    """Load sensor data from JSON file"""
    with open(file_path, 'r') as file:
        return json.load(file)

def find_activities(sensor_data):
    """Extract activities with begin/end markers from sensor data"""
    activities = []
    current_activity = None
    
    for entry in sensor_data:
        if entry['activity']:
            # Clean and parse description
            desc = entry['activity'].lower().strip()
            if ',begin' in desc:
                # Start new activity
                current_activity = {
                    'name': entry['activity'].split(',')[0].strip(),
                    'start': f"{entry['date']} {entry['time']}",
                    'sensor': entry['sensor'],
                    'state': entry['state']
                }
            elif ',end' in desc and current_activity is not None:
                # Validate sensor match before ending activity
                if current_activity['sensor'] == entry['sensor']:
                    current_activity['end'] = f"{entry['date']} {entry['time']}"
                    activities.append(current_activity)
                    current_activity = None
                
    return activities

def analyze_activity_sequences(activities):
    # Sort activities by start time
    sorted_activities = sorted(
        activities,
        key=lambda x: datetime.strptime(x['start'], '%Y-%m-%d %H:%M:%S.%f')
    )

    # Create analysis structure
    analysis = {}
    
    for i, current in enumerate(sorted_activities):
        current_name = current['name']
        
        if current_name not in analysis:
            analysis[current_name] = {
                'precedentActivities': {},
                'followingActivities': {}
            }
        
        # Look for immediate predecessor
        if i > 0:
            prev = sorted_activities[i-1]['name']
            analysis[current_name]['precedentActivities'][prev] = \
                analysis[current_name]['precedentActivities'].get(prev, 0) + 1
        
        # Look for immediate follower
        if i < len(sorted_activities)-1:
            next_act = sorted_activities[i+1]['name']
            analysis[current_name]['followingActivities'][next_act] = \
                analysis[current_name]['followingActivities'].get(next_act, 0) + 1

    # Convert to final format
    result = []
    for activity, data in analysis.items():
        result.append({
            "activity": activity,
            "precedentActivities": sorted(
                [{"activity": k, "frequency": v} for k, v in data['precedentActivities'].items()],
                key=lambda x: (-x['frequency'], x['activity'])
            ),
            "followingActivities": sorted(
                [{"activity": k, "frequency": v} for k, v in data['followingActivities'].items()],
                key=lambda x: (-x['frequency'], x['activity'])
            )
        })
    
    return result

def save_results(results, output_file):
    """Save analysis results to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    input_file = "M&D_sensors.json"
    output_file = "activity_sequences.json"
    
    try:
        sensor_data = load_sensor_data(input_file)
        activities = find_activities(sensor_data)
        
        if not activities:
            print("No activities found in the sensor data!")
            return
            
        analysis_results = analyze_activity_sequences(activities)
        save_results(analysis_results, output_file)
        print(f"Successfully generated {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()