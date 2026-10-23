"""Sequential runs, bounded completions, durable evidence and cooperative cancellation."""

from copy import deepcopy
from datetime import datetime, timezone
import os
import threading
import time
import uuid

from .cases import CATEGORIES, TRIALS, evaluate, fingerprint, validate_case
from .provider import DEFAULT_SETTINGS, complete, validate_settings


def now():
    return datetime.now(timezone.utc).isoformat()


class Bench:
    def __init__(self, store, completion=complete, demo_delay=0.35):
        self.store, self.completion, self.demo_delay = store, completion, demo_delay
        self.lock = threading.RLock()
        self.active = None
        self.cancel_event = threading.Event()
        self.worker = None
        for run in store.all("run"):
            if run["status"] in ("running", "cancelling"):
                run["status"], run["finished_at"] = "interrupted", now()
                for item in run["results"]:
                    if item["status"] in ("running", "pending"):
                        item["status"] = "skipped"
                store.put("run", run["id"], run)

    def cases(self):
        customs = {case["id"]: case for case in self.store.all("case")}
        return [customs.pop(case["id"], deepcopy(case)) for case in TRIALS] + list(customs.values())

    def bootstrap(self):
        return {"cases": [{k: v for k, v in case.items() if k != "demo"} for case in self.cases()],
                "categories": CATEGORIES, "runs": self.runs(), "settings": self.settings(),
                "key_available": bool(os.environ.get("FORGEBENCH_LAB_API_KEY")), "active_run": self.active}

    def settings(self):
        return self.store.get("settings", "endpoint") or deepcopy(DEFAULT_SETTINGS)

    def save_settings(self, data):
        config = validate_settings(data)
        self.store.put("settings", "endpoint", config)
        return config

    def save_case(self, data):
        validated = validate_case(data)
        id = data.get("id")
        if id is not None and not isinstance(id, str):
            raise ValueError("Trial ID must be text.")
        if id and not any(case["id"] == id for case in self.cases()):
            raise ValueError("Trial not found.")
        validated.update(id=id or "custom-" + uuid.uuid4().hex[:12], origin="custom")
        with self.lock:
            self.store.put("case", validated["id"], validated)
        return validated

    def delete_case(self, id):
        if not self.store.get("case", id):
            raise ValueError("Only custom trials or local edits can be removed.")
        self.store.delete("case", id)

    def runs(self):
        return [{k: v for k, v in run.items() if k != "results"} for run in self.store.all("run")]

    def start(self, data):
        if not isinstance(data, dict):
            raise ValueError("Run settings must be an object.")
        mode, profile = data.get("mode", "demo"), data.get("profile", "candidate")
        if mode not in ("demo", "endpoint") or profile not in ("baseline", "candidate"):
            raise ValueError("Unknown model mode or demo profile.")
        ids = data.get("case_ids")
        if not isinstance(ids, list) or not ids or len(ids) > 100 or any(not isinstance(id, str) for id in ids):
            raise ValueError("Select between 1 and 100 trials.")
        available = {case["id"]: case for case in self.cases()}
        if len(set(ids)) != len(ids) or any(id not in available for id in ids):
            raise ValueError("Trial selection contains duplicates or unknown trials.")
        cases = [deepcopy(available[id]) for id in ids]
        config = validate_settings(self.settings()) if mode == "endpoint" else None
        with self.lock:
            if self.active:
                raise ValueError("A run is already active. Stop it or wait for completion.")
            id = "run-" + uuid.uuid4().hex[:12]
            run = {"id": id, "schema_version": "1.0.0", "started_at": now(), "finished_at": None,
                   "mode": mode, "model": config["model"] if config else f"Demo / {profile.title()}",
                   "endpoint": config["base_url"] if config else None,
                   "status": "running", "total": len(cases), "passed": 0, "failed": 0, "errors": 0,
                   "completed": 0, "duration_ms": 0,
                   "results": [{"case_id": case["id"], "title": case["title"], "category": case["category"],
                                "fingerprint": fingerprint(case), "case": {k: v for k, v in case.items() if k != "demo"},
                                "status": "pending", "response": None, "checks": [], "latency_ms": None, "error": None}
                               for case in cases]}
            self.store.put("run", id, run)
            self.active = id
            self.cancel_event = threading.Event()
            self.worker = threading.Thread(target=self._execute, args=(run, cases, config, profile), daemon=True)
            self.worker.start()
            return deepcopy(run)

    def cancel(self, id):
        with self.lock:
            if id != self.active:
                raise ValueError("That run is not active.")
            self.cancel_event.set()
            return {"status": "cancelling"}

    def _execute(self, run, cases, config, profile):
        started = time.monotonic()
        try:
            for item, case in zip(run["results"], cases):
                if self.cancel_event.is_set():
                    break
                item["status"] = "running"
                self.store.put("run", run["id"], run)
                tick = time.monotonic()
                try:
                    if config:
                        response = self.completion(case, config)
                    else:
                        if self.cancel_event.wait(self.demo_delay):
                            break
                        if "demo" not in case:
                            raise ValueError("This edited/custom trial has no demo fixture. Use a model endpoint.")
                        response = case["demo"][profile]
                    item["response"] = response
                    item["checks"] = evaluate(response, case["checks"])
                    item["status"] = "passed" if all(check["passed"] for check in item["checks"]) else "failed"
                except ValueError as exc:
                    item["status"], item["error"] = "error", str(exc)
                except Exception:
                    item["status"], item["error"] = "error", "Unexpected provider failure. No response could be evaluated."
                item["latency_ms"] = round((time.monotonic() - tick) * 1000) if config else None
                run["completed"] += 1
                run[{"passed": "passed", "failed": "failed", "error": "errors"}[item["status"]]] += 1
                run["duration_ms"] = round((time.monotonic() - started) * 1000)
                self.store.put("run", run["id"], run)
            for item in run["results"]:
                if item["status"] in ("pending", "running"):
                    item["status"] = "skipped"
            run["status"] = "cancelled" if self.cancel_event.is_set() else "completed"
        finally:
            run["finished_at"] = now()
            run["duration_ms"] = round((time.monotonic() - started) * 1000)
            self.store.put("run", run["id"], run)
            with self.lock:
                self.active = None

    def close(self):
        self.cancel_event.set()
        if self.worker:
            self.worker.join(timeout=47)
