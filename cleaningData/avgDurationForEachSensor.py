import json
from datetime import datetime, timedelta

# Load data from data.json
with open("data.json", "r") as file:
    data = json.load(file)

# Function to parse datetime
def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

# Dictionary to store durations for each activity
durations = {}

# Iterate through the data to find begin and end events
for entry in data:
    description = entry.get("description")
    if description:
        activity, event = description.split(',')
        if event == "begin":
            if activity not in durations:
                durations[activity] = []
            durations[activity].append({"begin": parse_datetime(entry["date"], entry["time"])})
        elif event == "end" and activity in durations:
            for duration in durations[activity]:
                if "end" not in duration:
                    duration["end"] = parse_datetime(entry["date"], entry["time"])
                    break

# Calculate the durations and averages
results = {}
for activity, times in durations.items():
    total_duration = timedelta()
    count = 0
    for time in times:
        if "end" in time:
            duration = time["end"] - time["begin"]
            total_duration += duration
            count += 1
    if count > 0:
        avg_duration = total_duration / count
        results[activity] = {
            "durations": [duration.total_seconds() for duration in [time["end"] - time["begin"] for time in times if "end" in time]],
            "average_duration": avg_duration.total_seconds()
        }

# Write the results to avgDurationForEachSensor.json
with open("avgDurationForEachSensor.json", "w") as file:
    json.dump(results, file, indent=4)