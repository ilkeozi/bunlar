from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawUnsSeriesPageIndex(Base):
    __tablename__ = "raw_uns_series_page_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    series: Mapped[str] = mapped_column(String(64), nullable=False)
    series_token: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_label: Mapped[str] = mapped_column(String(32), nullable=False)
    target_page: Mapped[int] = mapped_column(Integer, nullable=False)
    target_pdf_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_resolution: Mapped[str] = mapped_column(String(32), nullable=False)
    section_start_pdf_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_end_pdf_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    toc_page: Mapped[int] = mapped_column(Integer, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_page > 0", name="ck_raw_uns_series_idx_target_page_pos"),
        CheckConstraint("toc_page > 0", name="ck_raw_uns_series_idx_toc_page_pos"),
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "series_token",
            "target_page",
            name="uq_raw_uns_series_idx_natural",
        ),
        Index("ix_raw_uns_series_idx_token", "series_token"),
    )
