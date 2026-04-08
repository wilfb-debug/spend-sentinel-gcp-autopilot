import os
from datetime import datetime, timezone
from typing import Any

from google.cloud import asset_v1, bigquery

ASSET_TYPES = [
    "compute.googleapis.com/Instance",
    "compute.googleapis.com/Disk",
    "sqladmin.googleapis.com/Instance",
]


def build_row(asset: Any, project_id: str) -> dict[str, Any]:
    """Convert a single Cloud Asset Inventory asset into a BigQuery row."""
    resource = asset.resource if asset.resource else None
    location = resource.location if resource else "unknown"
    labels = dict(resource.data.get("labels", {})) if resource and resource.data else {}

    return {
        "resource_id": asset.name,
        "resource_type": asset.asset_type,
        "project_id": project_id,
        "location": location,
        "labels": str(labels),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_assets(
    asset_client: Any,
    project_id: str,
) -> list[dict[str, Any]]:
    """Fetch all tracked asset types from Cloud Asset Inventory."""
    if not project_id:
        raise ValueError("PROJECT_ID is required")

    request = asset_v1.ListAssetsRequest(
        parent=f"projects/{project_id}",
        asset_types=ASSET_TYPES,
        content_type=asset_v1.ContentType.RESOURCE,
    )

    rows = [build_row(asset, project_id) for asset in asset_client.list_assets(request)]

    return rows


def write_to_bigquery(
    bq_client: Any,
    table_id: str,
    rows: list[dict[str, Any]],
) -> list[Any]:
    """Insert inventory rows into BigQuery. Returns any insert errors."""
    if not rows:
        print("No assets collected — nothing to write.")
        return []

    errors: list[Any] = bq_client.insert_rows_json(table_id, rows)

    if errors:
        print(f"BigQuery insert errors: {errors}")
    else:
        print(f"Inventory written: {len(rows)} rows → {table_id}")

    return errors


def main() -> None:
    project_id: str = os.environ.get("PROJECT_ID", "")
    dataset: str = os.environ.get("DATASET", "spend_sentinel")
    table: str = os.environ.get("TABLE", "inventory")

    if not project_id:
        raise ValueError("PROJECT_ID environment variable is required")

    asset_client = asset_v1.AssetServiceClient()
    bq_client = bigquery.Client()
    table_id = f"{project_id}.{dataset}.{table}"

    rows = collect_assets(asset_client, project_id)
    errors = write_to_bigquery(bq_client, table_id, rows)

    if errors:
        raise RuntimeError(f"Failed to insert {len(errors)} row(s) into BigQuery")


if __name__ == "__main__":
    main()
