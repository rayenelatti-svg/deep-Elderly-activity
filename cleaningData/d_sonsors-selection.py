import json
from datetime import datetime

# Load data from data.json
with open("data.json", "r") as file:
    data = json.load(file)

# Filter D sensors and sort by date and time
d_sensors = [entry for entry in data if entry["sensor"].startswith("D")]

def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

d_sensors.sort(key=lambda x: parse_datetime(x['date'], x['time']))

# Load existing data from M&D_sensors.json
try:
    with open("M&D_sensors.json", "r") as file:
        md_sensors = json.load(file)
except FileNotFoundError:
    md_sensors = []

# Merge and sort the combined data
combined_sensors = md_sensors + d_sensors
combined_sensors.sort(key=lambda x: parse_datetime(x['date'], x['time']))

# Write the combined data back to M&D_sensors.json
with open("M&D_sensors.json", "w") as file:
    json.dump(combined_sensors, file, indent=4)