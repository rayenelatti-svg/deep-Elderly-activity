import json

def filter_events(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    filtered_events = []
    inside_event = False

    for event in data:
        if event.get('activity') and 'begin' in event['activity']:
            inside_event = True
        elif event.get('activity') and 'end' in event['activity']:
            inside_event = False
        if inside_event or event.get('activity'):
            filtered_events.append(event)

    with open(output_file, 'w') as f:
        json.dump(filtered_events, f, indent=4)

input_file = 'M_and_D_sensors.json'
output_file = 'M_and_D_sensors_filtered.json'
filter_events(input_file, output_file)