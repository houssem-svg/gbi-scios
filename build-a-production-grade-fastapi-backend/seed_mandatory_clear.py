"""Seed the mandatory list with 3 clear materials: Steel, Cement, Cables.

Run from the backend root:
    python seed_mandatory_clear.py

This script:
  1. Clears any existing mandatory_list_items rows (so you start fresh).
  2. Inserts 3 items with item_codes that EXACTLY match the test BoQ CSV:
       STEEL-001  → Steel Reinforcement Rebar
       CEMENT-001 → Portland Cement
       CABLE-001  → Low Voltage Power Cables
  3. All are marked mandatory=True so the compliance scan will flag any
     imported BoQ item whose item_code OR description fuzzy-matches.

The penalty rate (25%) is applied by compliance_service.DEFAULT_PENALTY_PERCENTAGE
at scan time — it is NOT stored on the mandatory item itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package is importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal  # noqa: E402
from app.models.mandatory_list import (  # noqa: E402
    MandatoryListItem,
    MandatoryStatus,
)
from sqlalchemy import delete, select  # noqa: E402


SEED_ITEMS = [
    {
        "item_code": "STEEL-001",
        "product_name": "Steel Reinforcement Rebar",
        "category": "Structural",
        "local_manufacturer": "Saudi Steel Pipe Co.",
        "mandatory_status": MandatoryStatus.MANDATORY,
    },
    {
        "item_code": "CEMENT-001",
        "product_name": "Portland Cement",
        "category": "Material",
        "local_manufacturer": "Yamama Cement Co.",
        "mandatory_status": MandatoryStatus.MANDATORY,
    },
    {
        "item_code": "CABLE-001",
        "product_name": "Low Voltage Power Cables",
        "category": "Electrical",
        "local_manufacturer": "Saudi Cables Co.",
        "mandatory_status": MandatoryStatus.MANDATORY,
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        # 1. Clear existing items so the seed is idempotent.
        db.execute(delete(MandatoryListItem))
        db.commit()
        print("✓ Cleared existing mandatory_list_items.")

        # 2. Insert the 3 seed items.
        for item_data in SEED_ITEMS:
            db.add(MandatoryListItem(**item_data))
        db.commit()
        print(f"✓ Inserted {len(SEED_ITEMS)} mandatory items:")

        # 3. Verify.
        for it in db.scalars(select(MandatoryListItem)).all():
            print(
                f"    - {it.item_code} | {it.product_name} | "
                f"category={it.category} | status={it.mandatory_status.value}"
            )
        print()
        print("Done. Now upload the matching test_boq_mandatory.csv to see violations.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
