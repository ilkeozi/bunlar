from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebFrontierScoreRule(Base):
    __tablename__ = "raw_web_frontier_score_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_type: Mapped[str] = mapped_column(String(16), nullable=False, default="contains")
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("match_type", "pattern", name="uq_raw_web_frontier_score_rule"),
        Index("ix_raw_web_frontier_score_rule_enabled_priority", "enabled", "priority"),
    )

