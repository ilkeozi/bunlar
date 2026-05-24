from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebPdfCandidate(Base):
    __tablename__ = "raw_web_pdf_candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    source_page_url: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_url: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "pdf_url",
            name="uq_raw_web_pdf_candidate_natural",
        ),
        Index("ix_raw_web_pdf_candidate_pdf_url", "pdf_url"),
        Index("ix_raw_web_pdf_candidate_score", "score"),
    )
