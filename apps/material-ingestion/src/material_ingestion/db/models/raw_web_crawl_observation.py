from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebHttpFetchAttempt(Base):
    __tablename__ = "raw_web_http_fetch_attempt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    crawl_run_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_run.id", ondelete="CASCADE"), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    requested_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    final_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    redirect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_http_fetch_attempt_uri_outcome_completed", "uri_identity_id", "outcome", "completed_at"),
        Index("ix_raw_web_http_fetch_attempt_run_id", "crawl_run_id", "id"),
    )


class RawWebHttpRepresentation(Base):
    __tablename__ = "raw_web_http_representation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fetch_attempt_id: Mapped[int] = mapped_column(ForeignKey("raw_web_http_fetch_attempt.id", ondelete="CASCADE"), nullable=False)
    storage_ref: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    etag: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_modified: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    cache_control: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_language: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content_encoding: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content_disposition: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_location: Mapped[str] = mapped_column(Text, nullable=False, default="")
    link: Mapped[str] = mapped_column(Text, nullable=False, default="")
    vary: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    allow: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    accept_ranges: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    server: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    x_robots_tag: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    retry_after: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    expires_full_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    metadata_only_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RawWebExtractedLink(Base):
    __tablename__ = "raw_web_extracted_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    target_uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    rel: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    anchor_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_extracted_link_target_uri_identity_id", "target_uri_identity_id"),
        UniqueConstraint("source_uri_identity_id", "target_uri_identity_id", name="uq_raw_web_extracted_link_source_target"),
    )


class RawWebPageMetadata(Base):
    __tablename__ = "raw_web_page_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    canonical_hint: Mapped[str] = mapped_column(Text, nullable=False, default="")
    robots_meta_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    hreflang_map_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RawWebStructuredDataRecord(Base):
    __tablename__ = "raw_web_structured_data_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="jsonld")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RawWebCandidateDocument(Base):
    __tablename__ = "raw_web_candidate_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    source_uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    classification: Mapped[str] = mapped_column(String(64), nullable=False, default="new")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distinct_source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_reason_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    decision_state: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    decision_reason_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("uri_identity_id", "source_uri_identity_id", name="uq_raw_web_candidate_document_unique"),
        Index("ix_raw_web_candidate_document_uri", "uri_identity_id"),
        Index("ix_raw_web_candidate_document_decision_state", "decision_state"),
    )
