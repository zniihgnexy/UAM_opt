import pandas as pd
import numpy as np

def load_and_preprocess(data_file):
    """
    Load the dataset and preprocess it by computing distance, time spent, and rush hour rolling window.
    """
    # Load data
    data = pd.read_csv(data_file)
    
    data['time_on'] = pd.to_datetime(data['time_on'])
    data['time_off'] = pd.to_datetime(data['time_off'])
    
    data['distance'] = np.sqrt((data['lat_on'] - data['lat_off'])**2 + (data['lon_on'] - data['lon_off'])**2)
    
    data['time_spend'] = (data['time_off'] - data['time_on']).dt.total_seconds() / 60
    
    rush_hour_period = 180
    data['rush_hour'] = data['time_spend'].rolling(window=rush_hour_period, min_periods=1).mean()
    
    return data

def classify_rush_hours(data):
    """
    Classify time steps into rush hour and non-rush hour based on the 75th percentile of demand.
    """
    rush_hour_threshold = data['rush_hour'].quantile(0.75)  # Top 25% of demand time steps
    data['rush_status'] = np.where(data['rush_hour'] >= rush_hour_threshold, 'rush', 'non_rush')
    return data

def assign_travel_modes(data):
    """
    Assign travel mode preferences (UAM or Non-UAM) based on distance level and rush hour status.
    """
    distance_threshold = data['distance'].quantile(0.40)
    data['distance_level'] = np.where(data['distance'] <= distance_threshold, 'short', 'long')

    data['UAM'] = 0
    uam_probabilities = {
        ('rush', 'short'): 0.4,  # 40% of short trips use UAM during rush hours
        ('rush', 'long'):  0.7,  # 70% of long trips use UAM during rush hours
        ('non_rush', 'short'): 0.3,  # 30% of short trips use UAM during non-rush hours
        ('non_rush', 'long'):  0.8   # 80% of long trips use UAM during non-rush hours
    }

    for (rush_status, distance_level), prob in uam_probabilities.items():
        mask = (data['rush_status'] == rush_status) & (data['distance_level'] == distance_level)
        data.loc[mask, 'UAM'] = np.random.choice([0, 1], size=mask.sum(), p=[1 - prob, prob])
    
    return data

def main(data_file, output_file):
    """
    Main function to process data, classify rush hours, assign UAM choices, and save the final dataset.
    """
    data = load_and_preprocess(data_file)
    data = classify_rush_hours(data)
    data = assign_travel_modes(data)

    data.to_csv(output_file, index=False)
    print(f"Processed data saved to {output_file}")


def UAM_data(data_file, output_file):
    """
    Main function to process data, classify rush hours, assign UAM choices, and save the final dataset.
    """
    data = load_and_preprocess(data_file)
    data = classify_rush_hours(data)
    data = assign_travel_modes(data)

    data.to_csv(output_file, index=False)
    print(f"Processed data saved to {output_file}")

    data_UAM = data[data['UAM'] == 1]
    data_UAM = data_UAM.drop(colomns = ['distance_level', 'rush_status', 'UAM'])
    data_UAM.to_csv('UAM_travel_data.csv', index=False)


data_file = 'save_od_with_id.csv'
output_file = 'UAM_travel_data.csv'
main(data_file, output_file)