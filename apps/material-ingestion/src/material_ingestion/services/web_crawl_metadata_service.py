from __future__ import annotations

import json

from bs4 import BeautifulSoup

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebPageMetadata


def extract_page_metadata(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html or "", "html.parser")
    canonical = ""
    robots = ""
    hreflang_map: dict[str, str] = {}

    canonical_tag = soup.find("link", attrs={"rel": lambda value: value and "canonical" in value})
    if canonical_tag is not None:
        canonical = str(canonical_tag.get("href", "") or "")

    robots_tag = soup.find("meta", attrs={"name": lambda value: str(value).lower() == "robots"})
    if robots_tag is not None:
        robots = str(robots_tag.get("content", "") or "")

    for link in soup.find_all("link"):
        rel = link.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        if "alternate" not in [str(r).lower() for r in rel]:
            continue
        lang = str(link.get("hreflang", "") or "").strip()
        href = str(link.get("href", "") or "").strip()
        if lang and href:
            hreflang_map[lang] = href

    return {
        "canonical_hint": canonical,
        "robots_meta": robots,
        "hreflang_map": hreflang_map,
    }


def persist_page_metadata(*, uri_identity_id: int, metadata: dict[str, object]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebPageMetadata(
            uri_identity_id=uri_identity_id,
            canonical_hint=str(metadata.get("canonical_hint", "") or ""),
            robots_meta_json=json.dumps({"robots": metadata.get("robots_meta", "")}, sort_keys=True),
            hreflang_map_json=json.dumps(metadata.get("hreflang_map", {}), sort_keys=True),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
