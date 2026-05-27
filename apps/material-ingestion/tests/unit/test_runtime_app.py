import json
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from material_ingestion.runtime_app import RunRequest, RuntimeState, _run_worker_loop, build_app


def _endpoint(path: str, state: RuntimeState | None = None, method: str | None = None):
    app = build_app(state or RuntimeState())
    method_upper = method.upper() if method else None
    route = next(
        route
        for route in app.routes
        if getattr(route, "path", None) == path
        and (method_upper is None or method_upper in getattr(route, "methods", set()))
    )
    return route.endpoint


class RuntimeAppRunsTest(unittest.TestCase):
    def test_create_run_accepts_valid_request(self) -> None:
        endpoint = _endpoint("/runs", method="POST")
        req = RunRequest(seed_url="https://www.basf.com", max_pages=20, cross_domain=False, ingest_source="web_discovery")
        with (
            patch("material_ingestion.runtime_app.is_host_allowlisted", return_value=True),
            patch("material_ingestion.runtime_app.enqueue_core_discover_event", return_value=123) as enqueue_event,
        ):
            result = endpoint(req)
        self.assertTrue(result["accepted"])
        self.assertEqual(123, result["event_id"])
        self.assertEqual("core_discover_requested", result["event_type"])
        enqueue_event.assert_called_once()

    def test_create_run_rejects_non_http_url(self) -> None:
        endpoint = _endpoint("/runs", method="POST")
        req = RunRequest(seed_url="ftp://example.com")
        result = endpoint(req)
        self.assertEqual(400, result.status_code)
        body = json.loads(result.body.decode("utf-8"))
        self.assertEqual("invalid_seed_url", body["error"]["code"])

    def test_create_run_rejects_when_runtime_stopping(self) -> None:
        state = RuntimeState()
        state.stop_event.set()
        endpoint = _endpoint("/runs", state, method="POST")
        req = RunRequest(seed_url="https://www.basf.com")
        with patch("material_ingestion.runtime_app.is_host_allowlisted", return_value=True):
            result = endpoint(req)
        self.assertEqual(503, result.status_code)
        body = json.loads(result.body.decode("utf-8"))
        self.assertEqual("runtime_unavailable", body["error"]["code"])

    def test_create_run_returns_409_on_value_error(self) -> None:
        endpoint = _endpoint("/runs", method="POST")
        req = RunRequest(seed_url="https://www.basf.com")
        with (
            patch("material_ingestion.runtime_app.is_host_allowlisted", return_value=True),
            patch("material_ingestion.runtime_app.enqueue_core_discover_event", side_effect=ValueError("duplicate run key")),
        ):
            result = endpoint(req)
        self.assertEqual(409, result.status_code)
        body = json.loads(result.body.decode("utf-8"))
        self.assertEqual("run_conflict", body["error"]["code"])

    def test_create_run_returns_500_on_unexpected_error(self) -> None:
        endpoint = _endpoint("/runs", method="POST")
        req = RunRequest(seed_url="https://www.basf.com")
        with (
            patch("material_ingestion.runtime_app.is_host_allowlisted", return_value=True),
            patch("material_ingestion.runtime_app.enqueue_core_discover_event", side_effect=RuntimeError("db down")),
        ):
            result = endpoint(req)
        self.assertEqual(500, result.status_code)
        body = json.loads(result.body.decode("utf-8"))
        self.assertEqual("internal_error", body["error"]["code"])

    def test_create_run_rejects_non_allowlisted_host(self) -> None:
        endpoint = _endpoint("/runs", method="POST")
        req = RunRequest(seed_url="https://www.basf.com")
        with patch("material_ingestion.runtime_app.is_host_allowlisted", return_value=False):
            result = endpoint(req)
        self.assertEqual(403, result.status_code)
        body = json.loads(result.body.decode("utf-8"))
        self.assertEqual("host_not_allowlisted", body["error"]["code"])

    def test_trigger_evaluate_uses_default_batch_size(self) -> None:
        endpoint = _endpoint("/evaluate", method="POST")
        req = {"batch_size": 500}
        with patch("material_ingestion.runtime_app.enqueue_frontier_evaluate_event", return_value=123) as enqueue_event:
            result = endpoint(type("Req", (), req)())
        self.assertTrue(result["accepted"])
        self.assertEqual(123, result["event_id"])
        self.assertEqual("frontier_evaluate_requested", result["event_type"])
        enqueue_event.assert_called_once_with(batch_size=500)

class RuntimeAppSystemEndpointsTest(unittest.TestCase):
    def test_healthz_endpoint(self) -> None:
        endpoint = _endpoint("/healthz")
        self.assertEqual({"ok": True}, endpoint())

    def test_readyz_endpoint_ready(self) -> None:
        endpoint = _endpoint("/readyz")
        with patch("material_ingestion.runtime_app._is_db_ready", return_value=True):
            self.assertEqual({"ready": True}, endpoint())

    def test_readyz_endpoint_not_ready(self) -> None:
        endpoint = _endpoint("/readyz")
        with patch("material_ingestion.runtime_app._is_db_ready", return_value=False):
            with self.assertRaises(HTTPException) as ctx:
                endpoint()
        self.assertEqual(503, ctx.exception.status_code)
        self.assertEqual("not_ready", ctx.exception.detail)

    def test_version_endpoint_shape(self) -> None:
        endpoint = _endpoint("/version")
        out = endpoint()
        self.assertEqual("material-ingestion", out["service"])
        self.assertEqual("single-process", out["runtime"])
        self.assertIsInstance(out["pid"], int)

    def test_metrics_endpoint_reads_state(self) -> None:
        state = RuntimeState()
        state.worker_iterations = 7
        state.worker_errors = 2
        state.last_worker_rc = 1
        endpoint = _endpoint("/metrics", state)
        out = endpoint()
        self.assertIsInstance(out["uptime_seconds"], int)
        self.assertEqual(7, out["worker_iterations"])
        self.assertEqual(2, out["worker_errors"])
        self.assertEqual(1, out["last_worker_rc"])

    def test_metrics_core_endpoint_shape(self) -> None:
        endpoint = _endpoint("/metrics/core")

        class _Query:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        class _ExecResult:
            def __init__(self, payload):
                self._payload = payload

            def mappings(self):
                return self

            def first(self):
                return self._payload

        class _Session:
            def __init__(self):
                self._exec_calls = 0

            def query(self, *_args):
                return _Query(
                    [
                        ("core_discover_requested", "queued"),
                        ("frontier_build_requested", "running"),
                        ("frontier_fetch_requested", "done"),
                        ("frontier_evaluate_requested", "queued"),
                        ("frontier_get_requested", "running"),
                    ]
                )

            def execute(self, *_args, **_kwargs):
                self._exec_calls += 1
                if self._exec_calls == 1:
                    return _ExecResult(
                        {
                            "crawl_runs": 1,
                            "crawl_hosts": 2,
                            "sitemap_sources": 3,
                            "sitemap_entries": 4,
                            "sitemap_alternates": 5,
                            "frontier_items": 6,
                            "fetch_attempts": 7,
                            "http_representations": 8,
                            "decisions": 9,
                        }
                    )
                if self._exec_calls == 2:
                    return _ExecResult(
                        {
                            "frontier_total": 50,
                            "fetched": 30,
                            "evaluated": 20,
                            "promoted": 8,
                            "get_success": 5,
                            "candidate_count": 3,
                        }
                    )
                return _ExecResult(
                    {
                        "eval_eligible_not_evaluated": 12,
                        "eval_already_evaluated": 18,
                        "get_eligible_now": 4,
                    }
                )

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch("material_ingestion.runtime_app.create_session_factory", return_value=lambda: _Session()):
            out = endpoint()

        self.assertIn("runtime", out)
        self.assertIn("events", out)
        self.assertIn("backlog", out)
        self.assertIn("volumes", out)
        self.assertIn("funnel", out)
        self.assertIn("eligibility", out)
        self.assertEqual(2, out["events"]["queued"])
        self.assertEqual(1, out["backlog"]["build_running"])
        self.assertEqual(1, out["backlog"]["evaluate_queued"])
        self.assertEqual(1, out["backlog"]["get_running"])
        self.assertEqual(7, out["volumes"]["fetch_attempts"])
        self.assertEqual(8, out["funnel"]["promoted"])
        self.assertEqual(5, out["funnel"]["get_success"])
        self.assertEqual(12, out["eligibility"]["eval_eligible_not_evaluated"])
        self.assertEqual(18, out["eligibility"]["eval_already_evaluated"])
        self.assertEqual(4, out["eligibility"]["get_eligible_now"])


class RuntimeAppOpenApiTest(unittest.TestCase):
    def test_runs_openapi_contains_error_contracts(self) -> None:
        schema = build_app(RuntimeState()).openapi()
        responses = schema["paths"]["/runs"]["post"]["responses"]
        self.assertIn("400", responses)
        self.assertIn("409", responses)
        self.assertIn("500", responses)
        self.assertIn("503", responses)
        self.assertEqual("Invalid request semantics.", responses["400"]["description"])

    def test_openapi_includes_evaluation_rules_paths(self) -> None:
        schema = build_app(RuntimeState()).openapi()
        self.assertIn("/evaluation/rules", schema["paths"])
        self.assertIn("/evaluation/rules/{rule_id}", schema["paths"])


class RuntimeAppEvaluationRulesEndpointsTest(unittest.TestCase):
    def test_get_evaluation_rules_maps_response(self) -> None:
        endpoint = _endpoint("/evaluation/rules", method="GET")

        class _Rule:
            id = 5
            action = "promote"
            match_type = "contains"
            pattern = "/datasheet"
            weight = 10
            enabled = True
            priority = 40
            note = "promote datasheet urls"

        with patch("material_ingestion.runtime_app.list_evaluation_rules", return_value=[_Rule()]):
            out = endpoint()

        self.assertEqual(1, len(out))
        self.assertEqual("promote", out[0].action)
        self.assertEqual("/datasheet", out[0].pattern)


class RuntimeWorkerLoopTest(unittest.TestCase):
    def test_worker_loop_counts_non_zero_return_as_error(self) -> None:
        state = RuntimeState()

        def _fake_run(_args):
            state.stop_event.set()
            return 1

        with patch("material_ingestion.runtime_app.run_web_core_worker", side_effect=_fake_run):
            _run_worker_loop(state, sleep_seconds=0.01)

        self.assertEqual(1, state.worker_iterations)
        self.assertEqual(1, state.worker_errors)
        self.assertEqual(1, state.last_worker_rc)


class RuntimeRunStatusEndpointsTest(unittest.TestCase):
    def test_get_run_status_not_found(self) -> None:
        endpoint = _endpoint("/runs/{run_key}")

        class _Session:
            def query(self, _model):
                return self

            def filter(self, *_args):
                return self

            def order_by(self, *_args):
                return self

            def limit(self, *_args):
                return self

            def all(self):
                return []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch("material_ingestion.runtime_app.create_session_factory", return_value=lambda: _Session()):
            with self.assertRaises(HTTPException) as ctx:
                endpoint("missing-run")
        self.assertEqual(404, ctx.exception.status_code)

    def test_get_run_status_returns_history(self) -> None:
        endpoint = _endpoint("/runs/{run_key}")
        now = datetime.now(UTC)
        heartbeat = now - timedelta(seconds=42)

        class _Event:
            id = 9
            orchestration_id = "run-1"
            event_type = "core_discover_requested"
            status = "running"
            attempt_count = 1
            created_at = now
            started_at = now
            finished_at = None
            heartbeat_at = heartbeat
            error_text = ""
            updated_at = now

        class _Session:
            def query(self, _model):
                return self

            def filter(self, *_args):
                return self

            def order_by(self, *_args):
                return self

            def limit(self, *_args):
                return self

            def all(self):
                return [_Event()]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch("material_ingestion.runtime_app.create_session_factory", return_value=lambda: _Session()):
            out = endpoint("run-1")

        self.assertEqual("run-1", out.run_key)
        self.assertTrue(out.is_running)
        self.assertEqual("running", out.latest_status)
        self.assertEqual(1, len(out.events))

    def test_list_runs_returns_latest_per_run(self) -> None:
        endpoint = _endpoint("/runs", method="GET")
        now = datetime.now(UTC)

        class _Event:
            def __init__(self, event_id: int, run_key: str):
                self.id = event_id
                self.orchestration_id = run_key
                self.event_type = "core_discover_requested"
                self.status = "running"
                self.attempt_count = 1
                self.created_at = now
                self.started_at = now
                self.finished_at = None
                self.heartbeat_at = now
                self.error_text = ""
                self.updated_at = now

        class _Session:
            def query(self, _model):
                return self

            def order_by(self, *_args):
                return self

            def limit(self, *_args):
                return self

            def all(self):
                return [_Event(3, "run-a"), _Event(2, "run-a"), _Event(1, "run-b")]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        with patch("material_ingestion.runtime_app.create_session_factory", return_value=lambda: _Session()):
            out = endpoint(20)
        self.assertEqual(2, len(out.runs))
        self.assertEqual("run-a", out.runs[0].run_key)
        self.assertEqual("run-b", out.runs[1].run_key)
