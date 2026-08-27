from pathlib import Path

import pandas as pd


data_folder = Path("data/raw")
csv_files = sorted(data_folder.glob("*.csv"))

for file_path in csv_files:
    data = pd.read_csv(file_path)

    print()
    print("=" * 60)
    print(f"Fájl: {file_path.name}")
    print(f"Sorok száma: {data.shape[0]}")
    print(f"Oszlopok száma: {data.shape[1]}")
    print("Oszlopnevek:")

    for column in data.columns:
        print(f"  - {column}")