import pandas as pd
import json
import os

# File handling
base_folder = "LSTM_Model"
file_name = "M_and_D_sensors_labeled_chunked.json"
file_path = os.path.join(base_folder, file_name)

# Load JSON data
with open(file_path, 'r') as f:
    M_and_D_sensors_labeled_SensorsIntegration = json.load(f)

# Convert JSON data to DataFrame
df = pd.DataFrame(M_and_D_sensors_labeled_SensorsIntegration)

# Save DataFrame to CSV
csv_file_path = os.path.join(base_folder, "M_and_D_sensors_labeled_chunked.csv")
df.to_csv(csv_file_path, index=False)

print(f"Data successfully saved to {csv_file_path}")