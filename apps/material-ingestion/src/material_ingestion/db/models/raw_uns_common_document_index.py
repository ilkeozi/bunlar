from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawUnsCommonDocumentIndex(Base):
    __tablename__ = "raw_uns_common_document_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Ingestion metadata (source-agnostic, supports file/db/event ingestion later)
    ingest_source: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. uns_common_documents_index
    ingest_locator: Mapped[str] = mapped_column(Text, nullable=False)  # file path, object key, topic, etc.
    ingest_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)  # run id/version marker

    toc_page: Mapped[int] = mapped_column(Integer, nullable=False)
    document_code_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    document_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_label: Mapped[str] = mapped_column(String(64), nullable=False)
    target_page: Mapped[int] = mapped_column(Integer, nullable=False)

    page_resolution: Mapped[str] = mapped_column(String(32), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("toc_page > 0", name="ck_raw_uns_common_doc_toc_page_pos"),
        CheckConstraint("target_page > 0", name="ck_raw_uns_common_doc_target_page_pos"),
        CheckConstraint("char_length(document_code) > 0", name="ck_raw_uns_common_doc_code_nonempty"),
        UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "toc_page",
            "document_code",
            "target_page",
            name="uq_raw_uns_common_doc_natural",
        ),
        Index("ix_raw_uns_common_doc_code", "document_code"),
        Index("ix_raw_uns_common_doc_target_page", "target_page"),
        Index("ix_raw_uns_common_doc_toc_target", "toc_page", "target_page"),
    )
