"""Private Vercel service for the teaching warehouse and governed review operations."""
import base64
import gzip
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from threading import Lock

from fastapi import FastAPI

import agent
import build
import models
from web_service import execute

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_working = tempfile.TemporaryDirectory(prefix="northgate-")
_warehouse = Path(_working.name) / "warehouse.db"
_lock = Lock()


def warehouse():
    with _lock:
        if not _warehouse.exists():
            staging = _warehouse.with_suffix(".building")
            staging.unlink(missing_ok=True)
            with closing(sqlite3.connect(staging)) as db:
                db.execute("PRAGMA foreign_keys=ON")
                build.populate(db)
                db.commit()
            staging.replace(_warehouse)
    return agent.connect_data(_warehouse)


@app.post("/operate")
def operate(payload: dict):
    op = payload["op"]
    args = payload.get("args", {})
    if op == "prepare" and (args.get("apiKey") or args.get("mode") not in (models.GEMINI, models.RULES)):
        return {"error": "Choose Gemini API or Rules only. Hosted credentials are configured on the server."}
    with closing(warehouse()) as db, closing(agent.app_log(":memory:")) as log:
        if payload.get("state"):
            log.deserialize(gzip.decompress(base64.b64decode(payload["state"], validate=True)))
        changes = log.total_changes
        try:
            result = {"data": execute(op, args, warehouse=db, review_log=log)}
        except (ValueError, RuntimeError, sqlite3.IntegrityError) as exc:
            result = {"error": str(exc)}
        if log.total_changes > changes:
            result["state"] = base64.b64encode(gzip.compress(log.serialize())).decode("ascii")
        return result
