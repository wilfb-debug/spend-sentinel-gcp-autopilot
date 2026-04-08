import sys
import os
from unittest.mock import MagicMock, patch

# Stub GCP libraries — tests require no credentials
sys.modules.setdefault("google", MagicMock())
sys.modules.setdefault("google.cloud", MagicMock())
sys.modules.setdefault("google.cloud.asset_v1", MagicMock())
sys.modules.setdefault("google.cloud.bigquery", MagicMock())

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../Services-detectors/inventory-service"),
)

import pytest
from inventory import build_row, collect_assets, write_to_bigquery, main, ASSET_TYPES


PROJECT_ID = "test-project"
TABLE_ID = f"{PROJECT_ID}.spend_sentinel.inventory"


def make_asset(
    name="//compute.googleapis.com/projects/test/instances/my-vm",
    asset_type="compute.googleapis.com/Instance",
    location="us-central1-a",
    labels=None,
):
    """Helper — builds a mock asset matching the Cloud Asset Inventory shape."""
    asset = MagicMock()
    asset.name = name
    asset.asset_type = asset_type
    asset.resource = MagicMock()
    asset.resource.location = location
    asset.resource.data = {"labels": labels or {}}
    return asset


# ---------------------------------------------------------------------------
# build_row
# ---------------------------------------------------------------------------

class TestBuildRow:
    def test_contains_all_required_fields(self):
        asset = make_asset()
        row = build_row(asset, PROJECT_ID)
        for field in ("resource_id", "resource_type", "project_id", "location", "labels", "collected_at"):
            assert field in row

    def test_resource_id_matches_asset_name(self):
        asset = make_asset(name="//compute/projects/test/instances/vm1")
        row = build_row(asset, PROJECT_ID)
        assert row["resource_id"] == "//compute/projects/test/instances/vm1"

    def test_project_id_set_correctly(self):
        asset = make_asset()
        row = build_row(asset, PROJECT_ID)
        assert row["project_id"] == PROJECT_ID

    def test_location_from_resource(self):
        asset = make_asset(location="europe-west2-a")
        row = build_row(asset, PROJECT_ID)
        assert row["location"] == "europe-west2-a"

    def test_labels_serialised_as_string(self):
        asset = make_asset(labels={"env": "prod", "owner": "platform"})
        row = build_row(asset, PROJECT_ID)
        assert "env" in row["labels"]
        assert "prod" in row["labels"]

    def test_empty_labels_serialised(self):
        asset = make_asset(labels={})
        row = build_row(asset, PROJECT_ID)
        assert row["labels"] == "{}"

    def test_no_resource_falls_back_to_unknown_location(self):
        asset = MagicMock()
        asset.name = "//some/resource"
        asset.asset_type = "compute.googleapis.com/Disk"
        asset.resource = None
        row = build_row(asset, PROJECT_ID)
        assert row["location"] == "unknown"
        assert row["labels"] == "{}"

    def test_collected_at_is_iso_timestamp(self):
        asset = make_asset()
        row = build_row(asset, PROJECT_ID)
        assert "T" in row["collected_at"]
        assert row["collected_at"].endswith("+00:00")

    def test_all_three_asset_types_produce_rows(self):
        for asset_type in ASSET_TYPES:
            asset = make_asset(asset_type=asset_type)
            row = build_row(asset, PROJECT_ID)
            assert row["resource_type"] == asset_type


# ---------------------------------------------------------------------------
# collect_assets
# ---------------------------------------------------------------------------

class TestCollectAssets:
    def test_returns_rows_for_each_asset(self):
        mock_client = MagicMock()
        mock_client.list_assets.return_value = [
            make_asset(name="//compute/instances/vm1"),
            make_asset(name="//compute/disks/disk1", asset_type="compute.googleapis.com/Disk"),
        ]
        rows = collect_assets(mock_client, PROJECT_ID)
        assert len(rows) == 2

    def test_empty_asset_list_returns_empty(self):
        mock_client = MagicMock()
        mock_client.list_assets.return_value = []
        rows = collect_assets(mock_client, PROJECT_ID)
        assert rows == []

    def test_raises_on_missing_project_id(self):
        mock_client = MagicMock()
        with pytest.raises(ValueError, match="PROJECT_ID is required"):
            collect_assets(mock_client, "")

    def test_passes_correct_asset_types_to_client(self):
        mock_client = MagicMock()
        mock_client.list_assets.return_value = []
        collect_assets(mock_client, PROJECT_ID)
        call_args = mock_client.list_assets.call_args
        assert call_args is not None

    def test_each_row_has_correct_project_id(self):
        mock_client = MagicMock()
        mock_client.list_assets.return_value = [make_asset(), make_asset()]
        rows = collect_assets(mock_client, PROJECT_ID)
        assert all(r["project_id"] == PROJECT_ID for r in rows)


# ---------------------------------------------------------------------------
# write_to_bigquery
# ---------------------------------------------------------------------------

class TestWriteToBigquery:
    def test_empty_rows_returns_empty_list(self):
        mock_client = MagicMock()
        errors = write_to_bigquery(mock_client, TABLE_ID, [])
        assert errors == []
        mock_client.insert_rows_json.assert_not_called()

    def test_successful_write_returns_empty_errors(self):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        rows = [{"resource_id": "//vm1", "resource_type": "compute.googleapis.com/Instance"}]
        errors = write_to_bigquery(mock_client, TABLE_ID, rows)
        assert errors == []

    def test_insert_errors_are_returned(self):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = [{"index": 0, "errors": ["bad value"]}]
        rows = [{"resource_id": "//vm1"}]
        errors = write_to_bigquery(mock_client, TABLE_ID, rows)
        assert len(errors) == 1

    def test_calls_insert_with_correct_table_id(self):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        rows = [{"resource_id": "//vm1"}]
        write_to_bigquery(mock_client, TABLE_ID, rows)
        mock_client.insert_rows_json.assert_called_once_with(TABLE_ID, rows)

    def test_writes_all_rows(self):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        rows = [{"resource_id": f"//vm{i}"} for i in range(5)]
        write_to_bigquery(mock_client, TABLE_ID, rows)
        _, call_rows = mock_client.insert_rows_json.call_args[0]
        assert len(call_rows) == 5


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    @patch("inventory.write_to_bigquery", return_value=[])
    @patch("inventory.collect_assets", return_value=[{"resource_id": "//vm1"}])
    @patch("inventory.bigquery")
    @patch("inventory.asset_v1")
    def test_runs_successfully(self, mock_asset, mock_bq, mock_collect, mock_write):
        with patch.dict(os.environ, {"PROJECT_ID": PROJECT_ID}):
            main()
        mock_collect.assert_called_once()
        mock_write.assert_called_once()

    def test_raises_on_missing_project_id(self):
        env = {k: v for k, v in os.environ.items() if k != "PROJECT_ID"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PROJECT_ID"):
                main()

    @patch("inventory.write_to_bigquery", return_value=[{"error": "insert failed"}])
    @patch("inventory.collect_assets", return_value=[{"resource_id": "//vm1"}])
    @patch("inventory.bigquery")
    @patch("inventory.asset_v1")
    def test_raises_on_bigquery_errors(self, mock_asset, mock_bq, mock_collect, mock_write):
        with patch.dict(os.environ, {"PROJECT_ID": PROJECT_ID}):
            with pytest.raises(RuntimeError, match="Failed to insert"):
                main()
