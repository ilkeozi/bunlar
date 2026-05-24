from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from material_ingestion.db.base import Base


class RawWebUrlBlobMap(Base):
    __tablename__ = "raw_web_url_blob_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_seen_batch_id: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("canonical_source_url", name="uq_raw_web_url_blob_map_canonical_url"),
    )
