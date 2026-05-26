from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebCrawlRun(Base):
    __tablename__ = "raw_web_crawl_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_key: Mapped[str] = mapped_column(String(128), nullable=False)
    initiator: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    force_refresh: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("run_key", name="uq_raw_web_crawl_run_key"),)


class RawWebFrontierItem(Base):
    __tablename__ = "raw_web_frontier_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uri_identity_id: Mapped[int] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="CASCADE"), nullable=False)
    crawl_run_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_run.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state_reason_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_raw_web_frontier_item_uri_identity_id", "uri_identity_id"),
        Index("ix_raw_web_frontier_item_state", "state"),
        Index("ix_raw_web_frontier_item_run_state_priority_id", "crawl_run_id", "state", "priority", "id"),
    )


class RawWebCrawlDecision(Base):
    __tablename__ = "raw_web_crawl_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crawl_run_id: Mapped[int] = mapped_column(ForeignKey("raw_web_crawl_run.id", ondelete="CASCADE"), nullable=False)
    uri_identity_id: Mapped[int | None] = mapped_column(ForeignKey("raw_web_uri_identity.id", ondelete="SET NULL"), nullable=True)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (Index("ix_raw_web_crawl_decision_run", "crawl_run_id"),)
