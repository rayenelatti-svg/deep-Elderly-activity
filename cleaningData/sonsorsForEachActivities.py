
import json
activities = {
    "Meal_Preparation,begin": set(),
    "Meal_Preparation,end": set(),
    "Relax,begin": set(),
    "Relax,end": set(),
    "Eating,begin": set(),
    "Eating,end": set(),
    "Work,begin": set(),
    "Work,end": set(),
    "Sleeping,begin": set(),
    "Sleeping,end": set(),
    "Wash_Dishes,begin": set(),
    "Wash_Dishes,end": set(),
    "Bed_to_Toilet,begin": set(),
    "Bed_to_Toilet,end": set(),
    "Enter_Home,begin": set(),
    "Enter_Home,end": set(),
    "Leave_Home,begin": set(),
    "Leave_Home,end": set(),
    "Housekeeping,begin": set(),
    "Housekeeping,end": set(),
    "Respirate,begin": set(),
    "Respirate,end": set()
}
with open("M_sensors.json", "r") as file:
    data = json.load(file)

# Apply validation and modification
for d in data:
    if d['description'] in activities:
        activities[d['description']].add(d['sensor'])

with open("sonsorsForEachActivities.json", "w") as file:
    json.dump({k: list(v) for k, v in activities.items()}, file, indent=4)
print("Modifications terminées. Les données ont été enregistrées dans 'sonsorsForEachActivities.json'.")