from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebApiPageFetch(Base):
    __tablename__ = "raw_web_api_page_fetch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orchestration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_page_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    request_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    page_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    response_fingerprint_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    extracted_url_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_api_page_fetch_orch_id", "orchestration_id", "id"),
        Index("ix_raw_web_api_page_fetch_batch_id", "ingest_batch_id", "id"),
        Index("ix_raw_web_api_page_fetch_request_url", "request_url"),
    )
