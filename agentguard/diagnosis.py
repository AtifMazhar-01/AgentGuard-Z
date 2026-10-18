import json
import os
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from dotenv import load_dotenv
from google import genai
from google.genai import types

from agentguard.db import connect_mongodb


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

SYSTEM_INSTRUCTION = """
You are AgentGuard, an AI assistant for server reliability
and security investigation.

Rules:
1. Analyze only the telemetry and anomaly evidence provided.
2. An anomaly is not proof of a hardware failure, root cause,
   or security attack.
3. Clearly separate observed facts from possible explanations.
4. Rank probable causes and explain the supporting evidence.
5. Identify missing information and uncertainty.
6. Recommend safe diagnostic next steps.
7. Never claim to have executed an action.
8. Do not recommend destructive commands or disabling security.
9. If evidence is insufficient, explicitly say so.

Respond in concise Markdown with these sections:
## Summary
## Observed Evidence
## Probable Causes
## Missing Evidence
## Recommended Next Steps
## Safety Note
"""


def get_latest_anomaly(database, anomaly_id=None):
    anomalies = database["anomalies"]

    if anomaly_id is not None:
        try:
            anomaly_id = ObjectId(str(anomaly_id))
        except Exception as error:
            raise ValueError(
                "Invalid anomaly ID. Use a MongoDB ObjectId."
            ) from error

        anomaly = anomalies.find_one({"_id": anomaly_id})
    else:
        anomaly = anomalies.find_one(
            {},
            sort=[("detected_at", -1)],
        )

    if anomaly is None:
        raise ValueError(
            "No anomaly found. Run the monitoring process first."
        )

    return anomaly


def get_recent_telemetry(database, anomaly):
    query = {
        "schema_version": 1,
        "host_id": anomaly.get("host_id"),
    }

    anomaly_time = anomaly.get("timestamp")

    if anomaly_time is not None:
        query["timestamp"] = {"$lte": anomaly_time}

    records = list(
        database["telemetry"]
        .find(
            query,
            {
                "_id": 0,
                "host_id": 1,
                "timestamp": 1,
                "cpu_usage_percent": 1,
                "cpu_freq_mhz": 1,
                "cpu_temp_celsius": 1,
                "mem_usage_percent": 1,
                "mem_available_mb": 1,
                "swap_usage_percent": 1,
                "disk_usage_percent": 1,
                "disk_read_mb_s": 1,
                "disk_write_mb_s": 1,
                "net_download_mbps": 1,
                "net_upload_mbps": 1,
                "net_errors_in": 1,
                "net_errors_out": 1,
                "load_avg_1m": 1,
                "load_avg_5m": 1,
                "proc_count": 1,
            },
        )
        .sort("timestamp", -1)
        .limit(12)
    )

    # Put the oldest observation first.
    records.reverse()

    for record in records:
        timestamp = record.get("timestamp")

        if timestamp is not None:
            record["timestamp"] = timestamp.isoformat()

    return records


def diagnose_anomaly(anomaly_id=None):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from your .env file."
        )

    client, database = connect_mongodb()

    try:
        anomaly = get_latest_anomaly(database, anomaly_id)
        telemetry = get_recent_telemetry(database, anomaly)

        detected_at = anomaly.get("detected_at")

        if detected_at is not None:
            detected_at = detected_at.isoformat()

        # Send a compact evidence package, not the entire database.
        evidence = {
            "host_id": anomaly.get("host_id"),
            "anomaly_time": (
                anomaly.get("timestamp").isoformat()
                if anomaly.get("timestamp") is not None
                else None
            ),
            "detected_at": detected_at,
            "isolation_forest_score": anomaly.get("anomaly_score"),
            "model_status": anomaly.get("status"),
            "anomalous_feature_values": anomaly.get(
                "feature_values", {}
            ),
            "recent_telemetry": telemetry,
        }

        prompt = (
            "Investigate this AgentGuard server anomaly.\n\n"
            "Important: the Isolation Forest score is a model score, "
            "not a probability of an attack or failure. Use the "
            "provided evidence and state when it is insufficient.\n\n"
            "Evidence:\n"
            + json.dumps(evidence, indent=2, default=str)
        )

        gemini_client = genai.Client(api_key=api_key)

        try:
            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    max_output_tokens=1200,
                ),
            )
        finally:
            gemini_client.close()

        diagnosis_text = response.text

        if not diagnosis_text:
            raise RuntimeError(
                "Gemini returned an empty diagnosis."
            )

        diagnosis_document = {
            "anomaly_id": anomaly["_id"],
            "host_id": anomaly.get("host_id"),
            "created_at": datetime.now(timezone.utc),
            "model": MODEL_NAME,
            "diagnosis_text": diagnosis_text,
            "evidence_record_count": len(telemetry),
            "status": "completed",
        }

        result = database["diagnoses"].insert_one(
            diagnosis_document
        )

        return {
            "diagnosis_id": str(result.inserted_id),
            "host_id": anomaly.get("host_id"),
            "anomaly_id": str(anomaly["_id"]),
            "diagnosis_text": diagnosis_text,
        }

    finally:
        client.close()


def main():
    try:
        result = diagnose_anomaly()

        print("\nAI diagnosis generated successfully.")
        print("Host:", result["host_id"])
        print("Diagnosis ID:", result["diagnosis_id"])
        print("\n" + result["diagnosis_text"])

    except Exception as error:
        print(
            "Diagnosis failed:",
            type(error).__name__,
            error,
        )


if __name__ == "__main__":
    main()