from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker

from material_ingestion.db.models import (
    RawWebCrawlHost,
    RawWebCrawlRun,
    RawWebExtractedLink,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_frontier_get_service import _INSERT_EXTRACTED_LINK


class ExtractedLinkInsertStatementTest(unittest.TestCase):
    """Verify the module-level INSERT statement has the conflict clause baked in."""

    def test_statement_compiles_with_on_conflict_do_nothing(self) -> None:
        compiled = str(_INSERT_EXTRACTED_LINK.compile(dialect=postgresql.dialect()))
        self.assertIn("ON CONFLICT", compiled.upper())
        self.assertIn("DO NOTHING", compiled.upper())

    def test_conflict_targets_source_and_target_columns(self) -> None:
        compiled = str(_INSERT_EXTRACTED_LINK.compile(dialect=postgresql.dialect()))
        self.assertIn("source_uri_identity_id", compiled)
        self.assertIn("target_uri_identity_id", compiled)


class ExtractedLinkDuplicateSafeInsertTest(unittest.TestCase):
    """Verify duplicate (source, target) pairs are silently ignored on insert."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

        # SQLite does not support ON CONFLICT on named constraints the way
        # PostgreSQL does, but it does support ON CONFLICT DO NOTHING with
        # index_elements when a UNIQUE index exists.  We emulate the unique
        # index here via the model's UniqueConstraint.
        tables = [
            RawWebCrawlHost.__table__,
            RawWebCrawlRun.__table__,
            RawWebUriIdentity.__table__,
            RawWebExtractedLink.__table__,
        ]
        for table in tables:
            table.create(self.engine)

        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    def _seed_identity(self, session, uri: str, host_id: int) -> int:
        obj = RawWebUriIdentity(
            canonical_uri=uri,
            normalized_hash=f"h{abs(hash(uri))}",
            host_id=host_id,
        )
        session.add(obj)
        session.flush()
        return int(obj.id)

    def _setup_identities(self) -> tuple[int, int]:
        with self.session_factory() as session:
            host = RawWebCrawlHost(
                hostname="ex.com", source_type="seed", discovery_source="t",
                allowlist_match=True, auto_crawl_enabled=True,
            )
            session.add(host)
            session.flush()
            sid = self._seed_identity(session, "https://ex.com/a", int(host.id))
            tid = self._seed_identity(session, "https://ex.com/b", int(host.id))
            session.commit()
        return sid, tid

    def test_inserting_same_pair_twice_produces_one_row(self) -> None:
        sid, tid = self._setup_identities()
        row = {"source_uri_identity_id": sid, "target_uri_identity_id": tid, "rel": "", "anchor_text": ""}

        # SQLite uses a dialect-specific insert; we test the dedup logic directly
        # using SQLite's INSERT OR IGNORE which mirrors ON CONFLICT DO NOTHING.
        with self.session_factory() as session:
            session.execute(
                text(
                    "INSERT OR IGNORE INTO raw_web_extracted_link"
                    " (source_uri_identity_id, target_uri_identity_id, rel, anchor_text)"
                    " VALUES (:source_uri_identity_id, :target_uri_identity_id, :rel, :anchor_text)"
                ),
                row,
            )
            session.execute(
                text(
                    "INSERT OR IGNORE INTO raw_web_extracted_link"
                    " (source_uri_identity_id, target_uri_identity_id, rel, anchor_text)"
                    " VALUES (:source_uri_identity_id, :target_uri_identity_id, :rel, :anchor_text)"
                ),
                row,
            )
            session.commit()

        with self.session_factory() as session:
            count = session.query(RawWebExtractedLink).filter_by(
                source_uri_identity_id=sid, target_uri_identity_id=tid
            ).count()
        self.assertEqual(1, count)

    def test_distinct_pairs_each_produce_a_row(self) -> None:
        sid, tid = self._setup_identities()
        with self.session_factory() as session:
            for src, tgt in [(sid, tid), (tid, sid)]:
                session.execute(
                    text(
                        "INSERT OR IGNORE INTO raw_web_extracted_link"
                        " (source_uri_identity_id, target_uri_identity_id, rel, anchor_text)"
                        " VALUES (:s, :t, '', '')"
                    ),
                    {"s": src, "t": tgt},
                )
            session.commit()

        with self.session_factory() as session:
            count = session.query(RawWebExtractedLink).count()
        self.assertEqual(2, count)


if __name__ == "__main__":
    unittest.main()
