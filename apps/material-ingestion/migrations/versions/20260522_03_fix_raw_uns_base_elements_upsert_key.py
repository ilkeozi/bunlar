"""fix raw uns base elements natural key

Revision ID: 20260522_03
Revises: 20260522_02
Create Date: 2026-05-22 21:05:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_03"
down_revision: Union[str, Sequence[str], None] = "20260522_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate by new key, keeping latest row id.
    op.execute(
        sa.text(
            """
            DELETE FROM raw_uns_base_elements_index t
            USING raw_uns_base_elements_index d
            WHERE t.id < d.id
              AND t.ingest_source = d.ingest_source
              AND t.ingest_batch_id = d.ingest_batch_id
              AND t.row_order = d.row_order
            """
        )
    )

    op.drop_constraint("uq_raw_uns_base_natural", "raw_uns_base_elements_index", type_="unique")
    op.create_unique_constraint(
        "uq_raw_uns_base_natural",
        "raw_uns_base_elements_index",
        ["ingest_source", "ingest_batch_id", "row_order"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_raw_uns_base_natural", "raw_uns_base_elements_index", type_="unique")
    op.create_unique_constraint(
        "uq_raw_uns_base_natural",
        "raw_uns_base_elements_index",
        ["ingest_source", "ingest_batch_id", "element_name", "symbol", "uns_range"],
    )
