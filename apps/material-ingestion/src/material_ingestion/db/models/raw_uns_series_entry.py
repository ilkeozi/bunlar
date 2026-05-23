from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawUnsSeriesEntry(Base):
    __tablename__ = "raw_uns_series_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    series_token: Mapped[str] = mapped_column(String(32), nullable=False)
    series_description: Mapped[str] = mapped_column(Text, nullable=False)
    uns_code: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    chemical_composition_structured: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    chemical_composition_symbol_check: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    cross_reference_specifications_structured: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    cross_reference_specifications_check: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    entry_pdf_page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_pdf_page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    is_replaced: Mapped[bool] = mapped_column(Boolean, nullable=False)
    inactive_boxed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("entry_pdf_page_start > 0", name="ck_raw_uns_series_entry_start_page_pos"),
        CheckConstraint("entry_pdf_page_end >= entry_pdf_page_start", name="ck_raw_uns_series_entry_end_ge_start"),
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "series_token",
            "uns_code",
            name="uq_raw_uns_series_entry_natural",
        ),
        Index("ix_raw_uns_series_entry_uns_code", "uns_code"),
        Index("ix_raw_uns_series_entry_series_token", "series_token"),
    )
