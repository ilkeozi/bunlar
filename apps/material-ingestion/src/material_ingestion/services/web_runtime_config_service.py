from __future__ import annotations

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebRuntimeConfig


def list_runtime_configs(*, enabled_only: bool = False) -> list[RawWebRuntimeConfig]:
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebRuntimeConfig)
        if enabled_only:
            query = query.filter(RawWebRuntimeConfig.enabled.is_(True))
        rows = query.order_by(RawWebRuntimeConfig.config_key.asc(), RawWebRuntimeConfig.id.asc()).all()
        for row in rows:
            session.expunge(row)
        return rows


def create_runtime_config(*, config_key: str, config_value: str, enabled: bool = True, note: str = "") -> int:
    key = str(config_key or "").strip()
    if not key:
        raise ValueError("empty_config_key")
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebRuntimeConfig(
            config_key=key,
            config_value=str(config_value),
            enabled=bool(enabled),
            note=str(note or ""),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def update_runtime_config(
    *,
    config_id: int,
    config_key: str | None = None,
    config_value: str | None = None,
    enabled: bool | None = None,
    note: str | None = None,
) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebRuntimeConfig).filter(RawWebRuntimeConfig.id == int(config_id)).first()
        if row is None:
            return False
        if config_key is not None:
            key = str(config_key).strip()
            if not key:
                raise ValueError("empty_config_key")
            row.config_key = key
        if config_value is not None:
            row.config_value = str(config_value)
        if enabled is not None:
            row.enabled = bool(enabled)
        if note is not None:
            row.note = str(note)
        session.commit()
        return True


def delete_runtime_config(*, config_id: int) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebRuntimeConfig).filter(RawWebRuntimeConfig.id == int(config_id)).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def replace_runtime_configs(*, rows: list[dict[str, object]]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        session.query(RawWebRuntimeConfig).delete()
        for item in rows:
            key = str(item.get("config_key", "")).strip()
            if not key:
                raise ValueError("empty_config_key")
            session.add(
                RawWebRuntimeConfig(
                    config_key=key,
                    config_value=str(item.get("config_value", "")),
                    enabled=bool(item.get("enabled", True)),
                    note=str(item.get("note", "") or ""),
                )
            )
        session.commit()
        return len(rows)


def get_runtime_int_config(*, key: str, default: int) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebRuntimeConfig)
            .filter(RawWebRuntimeConfig.config_key == key, RawWebRuntimeConfig.enabled.is_(True))
            .first()
        )
    if row is None:
        return int(default)
    try:
        return int(str(row.config_value).strip())
    except Exception:
        return int(default)


def get_runtime_float_config(*, key: str, default: float) -> float:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebRuntimeConfig)
            .filter(RawWebRuntimeConfig.config_key == key, RawWebRuntimeConfig.enabled.is_(True))
            .first()
        )
    if row is None:
        return float(default)
    try:
        return float(str(row.config_value).strip())
    except Exception:
        return float(default)
