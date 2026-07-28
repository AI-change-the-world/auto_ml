"""Copy this file to add a platform-managed batch annotation script."""
from __future__ import annotations


definition = {"key": "example", "version": "1.0.0"}


def execute_batch(params, report):
    results = []
    for index, item in enumerate(params.get("items") or [], start=1):
        # item["local_path"] is a read-only task-local copy of the dataset asset.
        results.append({
            "batch_item_id": item["batch_item_id"],
            "status": "skipped",
            "message": "replace the template implementation",
        })
        report(processed=index, total=len(params.get("items") or []), message="template processed")
    return {"items": results}
