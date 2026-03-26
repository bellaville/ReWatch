import os
import matplotlib.pyplot as plt
import json
import pandas as pd
import numpy as np

IMU_TESTING_NAMES = {
    "imu_data_20260324175920.json": ("Drop 1", 1774389556547, 1774389557107),
    "imu_data_20260324180553.json": ("Drop 2", 1774389951337, 1774389951922),
    "imu_data_20260324182521.json": ("Drop 3", 1774391118502, 1774391119070),
    "imu_data_20260324182808.json": ("Drop 4", 1774391284538, 1774391285088),
    #"imu_data_20260324185347.json": ("Drop 5", 1774392824415, 1774392824999), # 5th Drop Test
}

DIRNAME = os.path.dirname(os.path.realpath(__file__)) + "/"

def display():
    """
    Creates and displays a 2x2 plot for labeled testing data
    """

    _, axs = plt.subplots(nrows=2, ncols=2)

    for i, (filename, (title, start_time, end_time)) in enumerate(IMU_TESTING_NAMES.items()):

        # Open file and load data
        with open(DIRNAME + filename) as f:
            js = json.load(f)

        # Create DF
        df = pd.DataFrame(js['data'])
        df = df.loc[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)] # Apply manual time scoping
        df['norm'] = df.apply(lambda row: np.linalg.norm(row[['x', 'y', 'z']]), axis=1)

        # Get correct location and plot
        ax = axs[i // 2][i % 2]
        ax.set_ylabel("Acceleration (m/s²)")
        ax.set_title(f"{title} ({(end_time - start_time) / 1000:.2f}s Drop, μ = {df['norm'].mean():.2f}, s² = {df['norm'].var():.2f})")
        df.plot('timestamp', ['x', 'y', 'z', 'norm'], ax=ax)

    plt.show()

        
if __name__ == "__main__":
    display()