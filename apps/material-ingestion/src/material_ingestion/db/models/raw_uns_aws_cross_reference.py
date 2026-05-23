from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawUnsAwsCrossReference(Base):
    __tablename__ = "raw_uns_aws_cross_reference"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    aws_spec: Mapped[str] = mapped_column(String(64), nullable=False)
    aws_designation: Mapped[str] = mapped_column(String(128), nullable=False)
    aws_designation_raw: Mapped[str] = mapped_column(String(128), nullable=False)
    uns: Mapped[str] = mapped_column(String(16), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("page > 0", name="ck_raw_uns_aws_page_pos"),
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "aws_spec",
            "aws_designation",
            "uns",
            name="uq_raw_uns_aws_natural",
        ),
        Index("ix_raw_uns_aws_uns", "uns"),
        Index("ix_raw_uns_aws_spec", "aws_spec"),
    )
