import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from agentguard.db import connect_mongodb


PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = PROJECT_DIR / "models" / "isolation_forest.joblib"

POLL_INTERVAL = 5


def load_model():
    """Load the trained model and its feature configuration."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "Trained model not found. Collect baseline data, "
            "run agentguard.features, then agentguard.train_model."
        )

    artifact = joblib.load(MODEL_FILE)

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    feature_medians = artifact["feature_medians"]

    return model, feature_columns, feature_medians


def prepare_record(record, feature_columns, feature_medians):
    """Prepare one new telemetry record for model inference."""

    values = {}

    for column in feature_columns:
        value = record.get(column)

        try:
            value = float(value)
        except (TypeError, ValueError):
            value = float(feature_medians.get(column, 0.0))

        if not np.isfinite(value):
            value = float(feature_medians.get(column, 0.0))

        if not np.isfinite(value):
            value = 0.0

        values[column] = value

    return pd.DataFrame([values], columns=feature_columns)


def main():
    model, feature_columns, feature_medians = load_model()
    client, database = connect_mongodb()

    telemetry = database["telemetry"]
    anomalies = database["anomalies"]

    # Ensure the same telemetry record cannot create
    # multiple anomaly documents.
    anomalies.create_index("telemetry_id", unique=True)

    # Skip historical telemetry at startup. Monitor only
    # records arriving after this process starts.
    latest = telemetry.find_one(
        {"schema_version": 1},
        {"_id": 1},
        sort=[("_id", -1)],
    )

    last_id = None

    if latest is not None:
        last_id = latest["_id"]

    print("AgentGuard real-time monitor started.")
    print("Polling MongoDB every", POLL_INTERVAL, "seconds.")
    print("Waiting for new telemetry records.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            query = {"schema_version": 1}

            if last_id is not None:
                query["_id"] = {"$gt": last_id}

            try:
                records = list(
                    telemetry.find(query).sort("_id", 1).limit(100)
                )
            except Exception as error:
                print("MongoDB read failed:", error)
                time.sleep(POLL_INTERVAL)
                continue

            for record in records:
                try:
                    features = prepare_record(
                        record,
                        feature_columns,
                        feature_medians,
                    )

                    prediction = int(model.predict(features)[0])
                    score = float(model.decision_function(features)[0])

                    if prediction == -1:
                        anomaly = {
                            "telemetry_id": record["_id"],
                            "host_id": record.get("host_id"),
                            "timestamp": record.get("timestamp"),
                            "detected_at": datetime.now(timezone.utc),
                            "anomaly_score": score,
                            "status": "detected",
                            "feature_values": features.iloc[0].to_dict(),
                        }

                        anomalies.update_one(
                            {"telemetry_id": record["_id"]},
                            {"$setOnInsert": anomaly},
                            upsert=True,
                        )

                        print(
                            f"ANOMALY | Host: {record.get('host_id')} "
                            f"| Score: {score:.4f}"
                        )
                    else:
                        print(
                            f"NORMAL | Host: {record.get('host_id')} "
                            f"| Score: {score:.4f}"
                        )

                except Exception as error:
                    print(
                        "Failed to process telemetry:",
                        record.get("_id"),
                        error,
                    )

                finally:
                    last_id = record["_id"]

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nAgentGuard monitor stopped.")

    finally:
        client.close()


if __name__ == "__main__":
    main()