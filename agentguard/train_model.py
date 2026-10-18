from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "ml_features.csv"
MODEL_FILE = PROJECT_DIR / "models" / "isolation_forest.joblib"

MINIMUM_RECORDS = 100


def load_training_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "ML features not found. Run agentguard.features first."
        )

    dataframe = pd.read_csv(DATA_FILE)

    if len(dataframe) < MINIMUM_RECORDS:
        raise ValueError(
            f"Only {len(dataframe)} records available. "
            f"Collect at least {MINIMUM_RECORDS} records before training."
        )

    # Convert any unexpected non-numeric values to missing values.
    dataframe = dataframe.apply(pd.to_numeric, errors="coerce")

    # Remove completely empty columns.
    dataframe = dataframe.dropna(axis=1, how="all")

    # Remove columns that have no variation.
    useful_columns = []

    for column in dataframe.columns:
        if dataframe[column].nunique(dropna=True) > 1:
            useful_columns.append(column)

    dataframe = dataframe[useful_columns]

    if dataframe.empty or len(useful_columns) == 0:
        raise ValueError(
            "No useful varying numeric features found."
        )

    # Fill occasional missing measurements using column medians.
    dataframe = dataframe.fillna(dataframe.median())

    return dataframe


def train_model():
    features = load_training_data()
    
    # Save the defaults needed when scoring new records.
    feature_medians = features.median().to_dict()

    model = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42,
    )

    model.fit(features)

    artifact = {
        "model": model,
        "feature_columns": list(features.columns),
        "feature_medians": feature_medians,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_records": len(features),
    }

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_FILE)

    print("Isolation Forest training completed.")
    print("Training records:", len(features))
    print("Selected features:", list(features.columns))
    print("Model saved to:", MODEL_FILE)


if __name__ == "__main__":
    train_model()