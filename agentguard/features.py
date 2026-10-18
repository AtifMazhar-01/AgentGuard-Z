from pathlib import Path

import pandas as pd

from agentguard.db import connect_mongodb


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

# Features initially selected for anomaly detection.
FEATURE_COLUMNS = [
    "cpu_usage_percent",
    "mem_usage_percent",
    "mem_available_mb",
    "swap_usage_percent",
    "disk_usage_percent",
    "disk_read_mb_s",
    "disk_write_mb_s",
    "net_download_mbps",
    "net_upload_mbps",
    "net_errors_in",
    "net_errors_out",
    "net_drops_in",
    "net_drops_out",
    "load_avg_1m",
    "load_avg_5m",
    "load_avg_15m",
    "proc_count",
]


def load_telemetry():
    """Fetch stored telemetry from MongoDB Atlas."""

    client, database = connect_mongodb()

    try:
        records = list(
            database["telemetry"].find(
                {"schema_version": 1},
                {"_id": 0},
            ).sort("timestamp", 1)
        )
    finally:
        client.close()

    if not records:
        raise ValueError(
            "No telemetry records found. "
            "Start the LinuxONE collector when data is needed."
        )

    dataframe = pd.DataFrame(records)

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"],
        utc=True,
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["timestamp", "host_id"]
    )

    dataframe = dataframe.drop_duplicates(
        subset=["host_id", "timestamp"]
    )

    return dataframe


def prepare_features(dataframe):
    """Select and clean numeric features for ML."""

    available = [
        column
        for column in FEATURE_COLUMNS
        if column in dataframe.columns
    ]

    if not available:
        raise ValueError(
            "None of the expected ML features were found."
        )

    features = dataframe[available].copy()

    for column in available:
        features[column] = pd.to_numeric(
            features[column],
            errors="coerce",
        )

    # Remove columns with no usable values.
    features = features.dropna(axis=1, how="all")

    if features.empty or features.shape[1] == 0:
        raise ValueError("No usable numeric features remain.")

    # Fill occasional missing values with each column's median.
    medians = features.median()
    features = features.fillna(medians)

    return features


def main():
    dataframe = load_telemetry()
    features = prepare_features(dataframe)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save a snapshot for inspection and offline experiments.
    dataframe.to_csv(
        DATA_DIR / "telemetry_snapshot.csv",
        index=False,
    )

    # Save only the numeric ML features.
    features.to_csv(
        DATA_DIR / "ml_features.csv",
        index=False,
    )

    print("Telemetry fetched successfully!")
    print("Records:", len(dataframe))
    print("ML features:", len(features.columns))
    print("Feature names:", list(features.columns))

    print("\nTelemetry time range:")
    print("From:", dataframe["timestamp"].min())
    print("To:", dataframe["timestamp"].max())

    print("\nPrepared ML data:")
    print(features.head())

    print("\nFiles saved:")
    print(DATA_DIR / "telemetry_snapshot.csv")
    print(DATA_DIR / "ml_features.csv")


if __name__ == "__main__":
    main()