from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebCandidateEvent(Base):
    __tablename__ = "raw_web_candidate_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orchestration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_page_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    pdf_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_candidate_event_orch_id", "orchestration_id", "id"),
        Index("ix_raw_web_candidate_event_batch_id", "ingest_batch_id", "id"),
        Index("ix_raw_web_candidate_event_pdf_url", "pdf_url"),
    )
