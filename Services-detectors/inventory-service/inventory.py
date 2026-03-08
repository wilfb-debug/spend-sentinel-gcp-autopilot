from google.cloud import asset_v1
from google.cloud import bigquery
import os
from datetime import datetime

PROJECT_ID = os.environ.get("PROJECT_ID")
DATASET = os.environ.get("DATASET")
TABLE = os.environ.get("TABLE")

asset_client = asset_v1.AssetServiceClient()
bq_client = bigquery.Client()

parent = f"projects/{PROJECT_ID}"

assets = asset_client.list_assets(
    request={
        "parent": parent,
        "asset_types": [
            "compute.googleapis.com/Instance",
            "compute.googleapis.com/Disk",
            "sqladmin.googleapis.com/Instance",
        ],
    }
)

rows = []

for asset in assets:
    rows.append(
        {
            "resource_id": asset.name,
            "resource_type": asset.asset_type,
            "project_id": PROJECT_ID,
            "location": asset.resource.location,
            "labels": str(asset.resource.data.get("labels", {})),
            "collected_at": datetime.utcnow().isoformat(),
        }
    )

table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

errors = bq_client.insert_rows_json(table_id, rows)

if errors:
    print(errors)
else:
    print("Inventory successfully written to BigQuery")
