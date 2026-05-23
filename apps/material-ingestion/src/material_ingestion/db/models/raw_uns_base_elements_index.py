from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawUnsBaseElementsIndex(Base):
    __tablename__ = "raw_uns_base_elements_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    element_name: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    uns_range: Mapped[str] = mapped_column(String(64), nullable=False)
    index_label: Mapped[str] = mapped_column(String(32), nullable=False)
    index_pdf_page: Mapped[int] = mapped_column(Integer, nullable=False)
    row_order: Mapped[int] = mapped_column(Integer, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("index_pdf_page > 0", name="ck_raw_uns_base_idx_page_pos"),
        CheckConstraint("row_order >= 0", name="ck_raw_uns_base_row_order_nonneg"),
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "row_order",
            name="uq_raw_uns_base_natural",
        ),
        Index("ix_raw_uns_base_symbol", "symbol"),
    )
