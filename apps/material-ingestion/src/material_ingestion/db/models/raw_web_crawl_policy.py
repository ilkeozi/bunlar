from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebRobotsPolicy(Base):
    __tablename__ = "raw_web_robots_policy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_host.id", ondelete="CASCADE"), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_blob: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluation_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (Index("ix_raw_web_robots_policy_host_id", "host_id"),)


class RawWebSitemapSource(Base):
    __tablename__ = "raw_web_sitemap_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_host.id", ondelete="CASCADE"), nullable=False)
    sitemap_url: Mapped[str] = mapped_column(Text, nullable=False)
    discovered_via: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    last_fetch_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("host_id", "sitemap_url", name="uq_raw_web_sitemap_source_unique"),
        Index("ix_raw_web_sitemap_source_host", "host_id"),
    )


class RawWebSitemapEntry(Base):
    __tablename__ = "raw_web_sitemap_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sitemap_source_id: Mapped[int] = mapped_column(ForeignKey("raw_web_sitemap_source.id", ondelete="CASCADE"), nullable=False)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    lastmod_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("sitemap_source_id", "uri_identity_id", name="uq_raw_web_sitemap_entry_unique"),
        Index("ix_raw_web_sitemap_entry_source", "sitemap_source_id"),
    )
