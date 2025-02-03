import json

# Define sensor categories
M0_sensors = [
    'M001', 'M002', 'M003', 'M004', 'M005', 'M006', 'M007', 'M008', 'M009',
    'M010', 'M011', 'M012', 'M013', 'M014', 'M015', 'M016', 'M017', 'M018',
    'M019', 'M020', 'M021', 'M022', 'M023', 'M024', 'M025', 'M026', 'M027',
    'M028', 'M029', 'M030', 'M031'
]

# Load the JSON data
with open("./ValidData.json", "r") as file:
    data = json.load(file)
l=[]
for d in data:
    if d['sensor'] not in M0_sensors :
        continue
    else:
        l.append(d)
data=l
with open("M_sensors.json", "w") as file:
    json.dump(data, file, indent=4)