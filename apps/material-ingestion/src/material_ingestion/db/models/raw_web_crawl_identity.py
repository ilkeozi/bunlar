from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebCrawlHost(Base):
    __tablename__ = "raw_web_crawl_host"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discovery_source: Mapped[str] = mapped_column(Text, nullable=False, default="")
    allowlist_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_crawl_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("hostname", name="uq_raw_web_crawl_host_hostname"),)


class RawWebUriIdentity(Base):
    __tablename__ = "raw_web_uri_identity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_uri: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    host_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_host.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("canonical_uri", name="uq_raw_web_uri_identity_uri"),
        UniqueConstraint("normalized_hash", name="uq_raw_web_uri_identity_hash"),
        Index("ix_raw_web_uri_identity_host_id", "host_id"),
    )


class RawWebUriAlias(Base):
    __tablename__ = "raw_web_uri_alias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    observed_uri: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("uri_identity_id", "observed_uri", name="uq_raw_web_uri_alias_unique"),
        Index("ix_raw_web_uri_alias_identity", "uri_identity_id"),
    )
