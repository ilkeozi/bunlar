from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebPageObservation(Base):
    __tablename__ = "raw_web_page_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    page_title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_html_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    raw_html_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_html_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anchor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    button_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    form_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_download_keywords: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "page_url",
            name="uq_raw_web_page_observation_natural",
        ),
        Index("ix_raw_web_page_observation_page_url", "page_url"),
    )
