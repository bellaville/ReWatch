import os
import matplotlib.pyplot as plt
import json
import pandas as pd
import numpy as np

IMU_TESTING_NAMES = {
    "imu_data_20260315122754.json": "Laying Upright", # Watch is laying upright on table
    "imu_data_20260315123349.json": "Laying Upside-Down", # Watch is laying upside-down on table
    "imu_data_20260315124440.json": "Side Buttons-Up", # Watch has buttons up on side
    "imu_data_20260315124738.json": "Side Buttons-Down", # Watch has buttons down on side
    "imu_data_20260315125100.json": "Upright", # Watch is upright
    "imu_data_20260315125441.json": "Upside Down", # Watch is upside side up
    "imu_data_20260315131818.json": "Upright 2", # Validation when watch is upright
    "imu_data_20260315132408.json": "Upright 3" # Validation x2 when watch is upright
}

DIRNAME = os.path.dirname(os.path.realpath(__file__)) + "/"

def display():
    """
    Creates and displays a 2x4 plot for labeled testing data
    """

    _, axs = plt.subplots(nrows=2, ncols=4)

    for i, (filename, title) in enumerate(IMU_TESTING_NAMES.items()):

        # Open file and load data
        with open(DIRNAME + filename) as f:
            js = json.load(f)

        # Create DF
        df = pd.DataFrame(js['data'])
        df = df.loc[(df['timestamp'] >= min(df['timestamp']) + 10000) & (df['timestamp'] <= max(df['timestamp']) - 10000)] # 10s padding to not capture accidental movement
        df['norm'] = df.apply(lambda row: np.linalg.norm(row[['x', 'y', 'z']]), axis=1)

        # Get correct location and plot
        ax = axs[i // 4][i % 4]
        df.plot('timestamp', ['x', 'y', 'z', 'norm'], ax=ax, title=title)

    plt.show()

        
if __name__ == "__main__":
    display()