"""Durable local stage gates and trial ledger. No API credentials are stored."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.research.spec import STAGES, canonical, digest, experiment_id, validate


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        directory = self.root / ".research"
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "state.sqlite", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
          id TEXT PRIMARY KEY, stage TEXT NOT NULL, spec_hash TEXT,
          candidate TEXT, candidate_hash TEXT, approvals TEXT NOT NULL DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS jobs (
          key TEXT PRIMARY KEY, experiment TEXT NOT NULL, kind TEXT NOT NULL,
          stage TEXT NOT NULL, request TEXT NOT NULL, status TEXT NOT NULL,
          operation_id TEXT, response TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS trials (
          key TEXT PRIMARY KEY, experiment TEXT NOT NULL, family TEXT NOT NULL,
          candidate TEXT NOT NULL, parameters TEXT NOT NULL, run_id TEXT,
          stage TEXT NOT NULL, result TEXT NOT NULL, eligibility INTEGER);
        """)

    def close(self):
        self.db.close()

    def register(self, spec):
        validate(spec)
        with self.db:
            self.db.execute("INSERT INTO experiments(id,stage) VALUES (?, 'DRAFT')", (spec["experiment_id"],))

    def state(self, exp):
        row = self.db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id(exp),)).fetchone()
        if row is None:
            raise ValueError("Experiment not registered; audit a valid specification first")
        return dict(row)

    def verify(self, spec):
        validate(spec)
        state = self.state(spec["experiment_id"])
        if state["spec_hash"] and state["spec_hash"] != digest(spec):
            raise ValueError("Frozen specification changed")
        return state

    def transition(self, spec, target, *, candidate=None, confirmation=None, human=False):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            state = self.verify(spec)
            current = STAGES.index(state["stage"])
            if current + 1 >= len(STAGES) or STAGES[current + 1] != target:
                raise ValueError(f"Illegal transition {state['stage']} -> {target}")
            approvals = json.loads(state["approvals"])
            prerequisite = {"WALK_FORWARD": "VALIDATION", "ROBUSTNESS": "WALK_FORWARD",
                            "TEST_COMPLETE": "TEST_AUTHORIZED"}.get(target)
            if prerequisite:
                rows = list(self.db.execute("SELECT status FROM jobs WHERE experiment=? AND stage=?",
                                            (spec["experiment_id"], prerequisite)))
                if not rows or any(r[0] not in ("COMPLETE", "COMPLETED") for r in rows):
                    raise ValueError(f"All {prerequisite} jobs must complete before advancing")
            if target in ("TEST_AUTHORIZED", "PAPER_AUTHORIZED"):
                artifact = "robustness.json" if target == "TEST_AUTHORIZED" else "final_review.json"
                path = self.root / "experiments" / spec["experiment_id"] / artifact
                if not path.exists():
                    raise ValueError(f"Reviewed evidence required: {artifact}")
                evidence = json.loads(path.read_text())
                if (evidence.get("spec_hash") != state["spec_hash"]
                        or evidence.get("candidate_hash") != state["candidate_hash"]
                        or evidence.get("review_complete") is not True):
                    raise ValueError("Review is incomplete or refers to different frozen inputs")
            if target in ("TEST_AUTHORIZED", "PAPER_AUTHORIZED"):
                action = "TEST" if target == "TEST_AUTHORIZED" else "PAPER"
                expected = f"OPEN {spec['experiment_id']} TEST" if action == "TEST" else f"DEPLOY {spec['experiment_id']} PAPER"
                if not human or confirmation != expected:
                    raise ValueError("Explicit interactive human confirmation required")
                if action == "TEST" and spec["windows"]["test"] is None:
                    raise ValueError("No historical Test specified")
                approvals[action] = {"confirmation": expected, "candidate_hash": state["candidate_hash"],
                                     "spec_hash": state["spec_hash"]}
            spec_hash = digest(spec) if target == "HYPOTHESIS_FROZEN" else state["spec_hash"]
            frozen, frozen_hash = state["candidate"], state["candidate_hash"]
            if target == "CANDIDATE_FROZEN":
                trials = list(self.db.execute("SELECT result,eligibility FROM trials WHERE experiment=? AND stage='DEVELOPMENT'",
                                              (spec["experiment_id"],)))
                if not trials or not any(row[1] == 1 for row in trials):
                    raise ValueError("At least one evidenced eligible Development trial required")
                if any(row[0] in ("SUBMITTING", "UNKNOWN", "SUBMITTED") for row in self.db.execute(
                        "SELECT status FROM jobs WHERE experiment=? AND stage='DEVELOPMENT'", (spec["experiment_id"],))):
                    raise ValueError("Resolve pending Development jobs before freezing")
                if not candidate or candidate.get("signal_count", 0) > spec["maximum_complexity"]:
                    raise ValueError("Candidate missing or exceeds complexity budget")
                if not candidate.get("portfolio") or not candidate.get("controls"):
                    raise ValueError("Candidate needs an inline portfolio and recorded controls")
                frozen, frozen_hash = canonical(candidate).decode(), digest(candidate)
            self.db.execute("UPDATE experiments SET stage=?,spec_hash=?,candidate=?,candidate_hash=?,approvals=? WHERE id=?",
                            (target, spec_hash, frozen, frozen_hash, json.dumps(approvals), spec["experiment_id"]))
        self.export(spec["experiment_id"])
        return self.state(spec["experiment_id"])

    def candidate(self, spec):
        state = self.verify(spec)
        if not state["candidate"]:
            raise ValueError("Candidate has not been frozen")
        result = json.loads(state["candidate"])
        if digest(result) != state["candidate_hash"]:
            raise ValueError("Candidate integrity failure")
        return result

    def record_trial(self, key, exp, family, candidate, parameters, stage, result, *, run_id=None, eligibility=None):
        # Rows are never removed; failures and unresolved submissions remain visible.
        with self.db:
            self.db.execute("""INSERT INTO trials VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(key) DO UPDATE SET run_id=excluded.run_id,result=excluded.result,eligibility=excluded.eligibility""",
                            (key, exp, family, candidate, json.dumps(parameters), run_id, stage,
                             json.dumps(result, allow_nan=False), eligibility))
        self.export(exp)

    def export(self, exp):
        directory = self.root / "experiments" / exp
        directory.mkdir(parents=True, exist_ok=True)
        state = self.state(exp)
        state["approvals"] = json.loads(state["approvals"])
        state["candidate"] = json.loads(state["candidate"]) if state["candidate"] else None
        trials = [dict(row) for row in self.db.execute("SELECT * FROM trials WHERE experiment=? ORDER BY key", (exp,))]
        for row in trials:
            row["result"], row["parameters"] = json.loads(row["result"]), json.loads(row["parameters"])
        for filename, value in (("state.json", state), ("trials.json", trials)):
            temporary = directory / (filename + ".tmp")
            temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            temporary.replace(directory / filename)


class RawStore:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, relative, response):
        target = self.root / relative
        if not target.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("Raw path escape")
        data = canonical(response)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != data:
                raise ValueError("Refusing to overwrite immutable raw response")
        else:
            # Exclusive creation; a racing writer cannot silently replace evidence.
            with target.open("xb") as handle:
                handle.write(data)
                handle.flush()
                import os
                os.fsync(handle.fileno())
        return {"path": str(relative), "sha256": digest(response)}

    def read(self, relative):
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root.resolve()):
            raise ValueError("Raw path escape")
        return json.loads(target.read_bytes())
