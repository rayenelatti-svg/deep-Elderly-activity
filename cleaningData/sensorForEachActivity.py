import json
from datetime import datetime

# Load data from M&D_sensors.json
print("Loading data from M&D_sensors.json...")
with open("M&D_sensors.json", "r") as file:
    data = json.load(file)
print(f"Loaded {len(data)} entries from M&D_sensors.json.")

# Function to parse datetime
def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

# Dictionary to store durations and sensor occurrences for each activity
durations = {}
sensor_occurrences = {}

# Iterate through the data to find begin and end events
print("Processing entries to find begin and end events...")
for entry in data:
    description = entry.get("description")
    if description:
        activity, event = description.split(',')
        if event == "begin":
            if activity not in durations:
                durations[activity] = []
                sensor_occurrences[activity] = {"activity": activity, "details": [], "total_sensors": {}}
            durations[activity].append({"begin": parse_datetime(entry["date"], entry["time"])})
        elif event == "end" and activity in durations:
            for duration in durations[activity]:
                if "end" not in duration:
                    duration["end"] = parse_datetime(entry["date"], entry["time"])
                    break
print("Finished processing begin and end events.")

# Calculate the sensor occurrences
print("Calculating sensor occurrences for each activity...")
for activity, times in durations.items():
    print(f"Processing activity: {activity}")
    for time in times:
        if "end" in time:
            print(f"Processing time range: {time['begin']} to {time['end']}")
            sensors = {}
            # Count the occurrences of each sensor between begin and end
            for entry in data:
                entry_time = parse_datetime(entry["date"], entry["time"])
                if time["begin"] <= entry_time <= time["end"]:
                    sensor = entry["sensor"]
                    if sensor not in sensors:
                        sensors[sensor] = 0
                    sensors[sensor] += 1
                    if sensor not in sensor_occurrences[activity]["total_sensors"]:
                        sensor_occurrences[activity]["total_sensors"][sensor] = 0
                    sensor_occurrences[activity]["total_sensors"][sensor] += 1
                    print(f"Sensor {sensor} triggered at {entry_time}, count: {sensors[sensor]}")
            sensor_occurrences[activity]["details"].append({
                "begin": time["begin"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                "end": time["end"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                "sensors": sensors
            })
            print(f"Finished processing time range: {time['begin']} to {time['end']}")
    print(f"Finished processing activity: {activity}")

# Write the results to sensorForEachActivity.json
print("Writing results to sensorForEachActivity.json...")
with open("sensorForEachActivity.json", "w") as file:
    json.dump(sensor_occurrences, file, indent=4)
print("Results saved to sensorForEachActivity.json")