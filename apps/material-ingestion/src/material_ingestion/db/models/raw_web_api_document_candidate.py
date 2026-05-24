from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebApiDocumentCandidate(Base):
    __tablename__ = "raw_web_api_document_candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orchestration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_page_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    response_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    document_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_api_document_candidate_orch_id", "orchestration_id", "id"),
        Index("ix_raw_web_api_document_candidate_batch_id", "ingest_batch_id", "id"),
        Index("ix_raw_web_api_document_candidate_document_url", "document_url"),
    )
