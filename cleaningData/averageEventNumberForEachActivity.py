import json
from datetime import datetime, timedelta

# Load data from data.json
print("Loading data from data.json...")
with open("M&D_sensors.json", "r") as file:
    data = json.load(file)
print(f"Loaded {len(data)} entries from data.json.")

# Function to parse datetime
def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

# Dictionary to store event details for each activity
event_details = {}

# Iterate through the data to track begin and end events
print("Processing entries to find begin and end events...")
for entry in data:
    description = entry.get("description")
    if description:
        activity, event = description.split(',')
        
        # Initialize activity if not exists
        if activity not in event_details:
            event_details[activity] = []
        
        # Track begin events
        if event == "begin":
            event_details[activity].append({
                "begin_date": entry["date"],
                "begin_time": entry["time"],
                "on_status_count": 0
            })
        
        # Match end events with corresponding begin events
        elif event == "end" and event_details[activity]:
            # Find the last unfinished begin event
            for event_group in reversed(event_details[activity]):
                if "end_date" not in event_group:
                    event_group["end_date"] = entry["date"]
                    event_group["end_time"] = entry["time"]
                    break
print("Finished processing begin and end events.")

# Count on status events for each activity
results = {}
averages = {}

for activity, events in event_details.items():
    print(f"Processing activity: {activity}")
    activity_results = {
        "event_counts": [],
    }
    
    # Process each begin-end pair
    event_counts = []
    on_status_list = []
    begin_end_pairs = 0
    
    for i, event in enumerate(events, 1):
        if "end_date" in event:
            begin_end_pairs += 1
            print(f"Processing event {i} for activity {activity}")
            # Count on status events between begin and end
            on_status_count = sum(
                1 for entry in data 
                if (parse_datetime(event["begin_date"], event["begin_time"]) <= 
                    parse_datetime(entry["date"], entry["time"]) <= 
                    parse_datetime(event["end_date"], event["end_time"]))
            )
            
            event_counts.append({
                "begin_date": event["begin_date"],
                "end_date": event["end_date"],
                "number_of_on_status": on_status_count
            })
            
            on_status_list.append(on_status_count)
            print(f"ON status count for event {i} for activity {activity}: {on_status_count}")
    
    # Calculate average event count
    if on_status_list:
        activity_results["event_counts"] = event_counts
        averages[activity] = sum(on_status_list) / len(on_status_list)
        print(f"Average ON status for activity {activity}: {averages[activity]}")
    
    results[activity] = activity_results
    print(f"Number of begin-end pairs for activity {activity}: {begin_end_pairs}")

# Write the results to avgEventCountForEachSensor.json
print("Writing results to avgEventCountForEachActivity.json...")
with open("avgEventCountForEachActivity.json", "w") as file:
    json.dump({
        "results": results,
        "averages": averages
    }, file, indent=4)
print("Analysis complete. Results saved to avgEventCountForEachActivity.json")