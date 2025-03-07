# Deep-Human-Activity-Recognition-in-smart-home
## Dataset Setup

1. Download the JSON file from Kaggle:  

2. Download the  M_and_D_sensors_labeled_AllSensors.json file from Kaggle: 

 This file is the result of the script activities-labeling. It consists of chunking the unlabeled data that is situated between the end of an activity and the beginning of another into chunks based on sudden changing sonsors and labeling them according to the files zoneTimeForEachActivity, Following&PrecedentActivitiesForEachActivity, and AllSensorsForEachActivities.
 



This project is organized into several folders to ensure better management of the different stages of data processing and LSTM model training for activity recognition.

📂 cleaningData
This folder contains the scripts and tools necessary for data preprocessing. This includes cleaning outliers, handling missing values, and normalizing data.

📂 documentation
Folder containing project documentation, including technical reports, model descriptions, and methodologies used.

📂 labelingMissingLine
Scripts for identifying and processing missing lines in the dataset, correctly labeling them based on abrupt sensor changes to avoid any loss of important information.

📂 LSTM_Model
Contains files related to the LSTM model, including the creation of appropriate input and model training (file "updated-cross-validation-with-time-features").

📂 scaler_and_dependencies
Folder grouping the necessary files to load the model and use it in other scripts.