import json
from datetime import datetime
from collections import defaultdict

# Charger les données depuis le fichier JSON
with open("M&D_sensors.json", "r") as f:
    events = json.load(f)

def parse_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

def categorize_time(timestamp):
    hour = timestamp.hour
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    else:
        return 'night'

def analyze_activity_patterns(events):
    # Structure pour stocker les intervalles
    activity_stats = defaultdict(lambda: {
        'start_times': {'morning': [], 'afternoon': [], 'night': []},
        'end_times': {'morning': [], 'afternoon': [], 'night': []},
        'durations': {'morning': [], 'afternoon': [], 'night': []}
    })
    
    # Stockage temporaire des activités commencées
    ongoing_activities = {}

    # Trier les événements par ordre chronologique
    sorted_events = sorted(events, key=lambda x: parse_datetime(x['date'], x['time']))

    for event in sorted_events:
        if not event['activity']:
            continue  # Ignorer les événements sans activité

        # Extraire le nom de l'activité et l'action (begin/end)
        activity_name, action = event['activity'].split(',')
        timestamp = parse_datetime(event['date'], event['time'])
        period = categorize_time(timestamp)

        if action == 'begin':
            # Stocker le début de l'activité
            ongoing_activities[activity_name] = (timestamp, period)
        elif action == 'end' and activity_name in ongoing_activities:
            # Récupérer le début de l'activité
            start_time, start_period = ongoing_activities.pop(activity_name)
            duration = (timestamp - start_time).total_seconds()  # Durée en secondes
            
            # Enregistrer les données
            activity_stats[activity_name]['start_times'][start_period].append(start_time)
            activity_stats[activity_name]['end_times'][period].append(timestamp)
            activity_stats[activity_name]['durations'][start_period].append(duration)

    # Calcul des moyennes
    results = {}
    for activity, stats in activity_stats.items():
        results[activity] = {
            'average_start_time': {},
            'average_end_time': {},
            'average_duration': {}
        }
        for period in ['morning', 'afternoon', 'night']:
            if stats['durations'][period]:
                # Calcul de la durée moyenne
                avg_duration = sum(stats['durations'][period]) / len(stats['durations'][period])
                
                # Calcul des heures moyennes de début et de fin
                avg_start = sum(t.hour + t.minute / 60 for t in stats['start_times'][period]) / len(stats['start_times'][period])
                avg_end = sum(t.hour + t.minute / 60 for t in stats['end_times'][period]) / len(stats['end_times'][period])
                
                # Formatage des résultats
                results[activity]['average_start_time'][period] = f"{int(avg_start):02d}:{int((avg_start % 1) * 60):02d}"
                results[activity]['average_end_time'][period] = f"{int(avg_end):02d}:{int((avg_end % 1) * 60):02d}"
                results[activity]['average_duration'][period] = f"{int(avg_duration)} seconds"
    
    return results

# Exécution de l'analyse
analysis = analyze_activity_patterns(events)

# Enregistrement des résultats dans un fichier JSON
with open("zoneTimeForEachActivity.json", "w") as f:
    json.dump(analysis, f, indent=4)

print("Les résultats ont été enregistrés dans 'zoneTimeForEachActivity.json'.")