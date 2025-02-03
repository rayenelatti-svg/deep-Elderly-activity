import json

# Load data from sensorForEachActivity.json
with open('sensorForEachActivity.json', 'r') as file:
    data = json.load(file)

# Extract activity names and their total sensor occurrences
activity_totals = {}
for activity, details in data['activity_sensor_occurrences'].items():
    activity_totals[activity] = details['total_sensor_occurrences']

# Write the extracted data to a new JSON file
with open('activityTotalSensorOccurrences.json', 'w') as outfile:
    json.dump(activity_totals, outfile, indent=2)

print("activityTotalSensorOccurrences.json generated successfully.")