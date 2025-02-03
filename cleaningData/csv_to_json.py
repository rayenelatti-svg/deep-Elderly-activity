import json

# Input and output file paths
input_file = "data.csv"
output_file = "data.json"

# Open the input file and parse lines into a list of dictionaries
data = []
with open(input_file, 'r') as file:
    for line in file:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Split the line into parts
        parts = line.strip().split(',')

        # Ensure the line has at least 3 parts (date, time, sensor)
        if len(parts) < 3:
            print(f"Skipping malformed line: {line.strip()}")
            continue
        
        # Create a dictionary for each line
        entry = {
            "date": parts[0],
            "time": parts[1],
            "sensor": parts[2],
            "state": parts[3] if len(parts) > 3 else None,
            "description": ','.join(parts[4:]) if len(parts) > 4 else None
        }
        data.append(entry)

# Write the parsed data to a JSON file
with open(output_file, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print("Conversion completed! JSON file saved as", output_file)
