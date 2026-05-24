from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebPageCrawl(Base):
    __tablename__ = "raw_web_page_crawl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    crawl_ok: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "page_url",
            name="uq_raw_web_page_crawl_natural",
        ),
        Index("ix_raw_web_page_crawl_page_url", "page_url"),
    )
