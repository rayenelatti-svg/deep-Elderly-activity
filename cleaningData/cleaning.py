import json

# Define sensor categories
M0_sensors = [
    'M001', 'M002', 'M003', 'M004', 'M005', 'M006', 'M007', 'M008', 'M009',
    'M010', 'M011', 'M012', 'M013', 'M014', 'M015', 'M016', 'M017', 'M018',
    'M019', 'M020', 'M021', 'M022', 'M023', 'M024', 'M025', 'M026', 'M027',
    'M028', 'M029', 'M030', 'M031'
]
D0_sensors = ["D001", "D002", "D003", "D004"]
T0_sensors = ["T001", "T002", "T003", "T004", "T005"]

# All sensors in one list
sensors = M0_sensors + D0_sensors + T0_sensors

# Load the JSON data
with open("data.json", "r") as file:
    data = json.load(file)

# Apply validation and modification
for d in data:

    # Ensure the sensor is in the valid list of sensors
    if d['sensor'] not in sensors:
        print(f"Erreur : Le capteur '{d['sensor']}' n'est pas dans la liste des capteurs valides : {d}")
        d.pop(d['sensor'])

for d in data:
    if d['sensor'] in M0_sensors :
        if d["state"] not in ["OFF", "ON"]:
            print(f"Erreur : L'état du capteur '{d['sensor']}' doit être 'ON' ou 'OFF' : {d}")
            if "OF" in d["state"]:
                d["state"] = "OFF"
            if   "ON" in d["state"]:
                d["state"] = "ON"
for d in data:
    if d['sensor'] in D0_sensors :
        if d["state"] not in ["OPEN", "CLOSE"]:
            print(f"Erreur : L'état du capteur '{d['sensor']}' doit être 'OPEN' ou 'CLOSE' : {d}")
            if "OP" in d["state"]:
                d["state"] = "OPEN"
            if   "CL" in d["state"]:
                d["state"] = "CLOSE"
           

for d in data:    # Check conditions for T0_sensors
    if d['sensor'] in T0_sensors:
        try:
            # Try converting the state to a float
            float(d["state"])
        except (ValueError, TypeError):
            print(f"Erreur : L'état du capteur '{d['sensor']}' doit être un nombre flottant : {d}")
            

# Write the modified data back to a new JSON file
with open("modified_data.json", "w") as file:
    json.dump(data, file, indent=4)

print("Modifications terminées. Les données ont été enregistrées dans 'modified_data.json'.")
