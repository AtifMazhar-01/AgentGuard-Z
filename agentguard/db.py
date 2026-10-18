import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


# Load configuration from the project root.
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


def connect_mongodb():
    """Connect to MongoDB Atlas and return the client and database."""

    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "agentguard")

    if not uri:
        raise ValueError("MONGODB_URI is missing from .env")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        appname="AgentGuard-Z",
    )

    try:
        client.admin.command("ping")
    except Exception:
        client.close()
        raise

    database = client[db_name]

    return client, database


def main():
    """Test the connection and retrieve stored telemetry."""

    client = None

    try:
        client, database = connect_mongodb()

        print("MongoDB connection successful!")

        telemetry = database["telemetry"]

        count = telemetry.count_documents(
            {"schema_version": 1}
        )

        print("Telemetry records found:", count)

        recent_records = telemetry.find(
            {"schema_version": 1},
            {
                "_id": 0,
                "host_id": 1,
                "timestamp": 1,
                "cpu_usage_percent": 1,
                "mem_usage_percent": 1,
                "proc_count": 1,
            },
        ).sort("timestamp", -1).limit(5)

        print("\nLatest telemetry records:")

        for record in recent_records:
            print(record)

    except Exception as error:
        print("Database test failed:")
        print(type(error).__name__, error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()