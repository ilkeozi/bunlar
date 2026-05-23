"""add aws designation raw column

Revision ID: 20260522_04
Revises: 20260522_03
Create Date: 2026-05-22 22:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_04"
down_revision: Union[str, Sequence[str], None] = "20260522_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "raw_uns_aws_cross_reference",
        sa.Column("aws_designation_raw", sa.String(length=128), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE raw_uns_aws_cross_reference
            SET aws_designation_raw = aws_designation
            WHERE aws_designation_raw IS NULL
            """
        )
    )
    op.alter_column("raw_uns_aws_cross_reference", "aws_designation_raw", nullable=False)


def downgrade() -> None:
    op.drop_column("raw_uns_aws_cross_reference", "aws_designation_raw")
