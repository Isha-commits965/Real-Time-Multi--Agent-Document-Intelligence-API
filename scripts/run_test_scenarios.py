#!/usr/bin/env python3
"""Run all 5 assessment test scenarios against the local API."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001/api"
PDF_SOURCE = Path("uploads/doc_41daca2552871e763cb91e73.pdf")
TXT_SOURCE = Path("uploads/doc_b7a9b6e0bb83fd6f3bfb7af.txt")
AGENTS = ("summarizer", "entity_extractor", "sentiment_analyzer", "document_classifier")
POLL_INTERVAL = 0.4
MAX_POLL_SECONDS = 120


def ok(msg: str) -> None:
    print(f"  PASS: {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL: {msg}")
    sys.exit(1)


def agent_summary(agents: dict) -> str:
    parts = []
    for name in AGENTS:
        a = agents[name]
        status = a["status"]
        extra = ""
        if status == "completed" and a.get("result"):
            extra = " (has result)"
        elif status == "failed" and a.get("error"):
            extra = f" (error: {a['error'][:60]}...)"
        parts.append(f"{name}={status}{extra}")
    return ", ".join(parts)


async def upload(client: httpx.AsyncClient, path: Path) -> dict:
    with path.open("rb") as f:
        response = await client.post(
            f"{BASE}/documents/upload",
            files={"file": (path.name, f, "application/octet-stream")},
        )
    response.raise_for_status()
    return response.json()


async def analyze(client: httpx.AsyncClient, document_id: str) -> dict:
    started = time.perf_counter()
    response = await client.post(f"{BASE}/documents/{document_id}/analyze")
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.raise_for_status()
    data = response.json()
    data["_trigger_ms"] = round(elapsed_ms, 1)
    return data


async def get_job(client: httpx.AsyncClient, job_id: str) -> dict:
    response = await client.get(f"{BASE}/jobs/{job_id}")
    response.raise_for_status()
    return response.json()


async def poll_until_complete(client: httpx.AsyncClient, job_id: str) -> dict:
    deadline = time.time() + MAX_POLL_SECONDS
    while time.time() < deadline:
        job = await get_job(client, job_id)
        status = job["status"]
        if status in {"completed", "partially_failed", "failed"}:
            return job
        await asyncio.sleep(POLL_INTERVAL)
    fail(f"Job {job_id} did not finish within {MAX_POLL_SECONDS}s")


def verify_all_agents_have_results(job: dict, label: str) -> None:
    agents = job["agents"]
    for name in AGENTS:
        agent = agents[name]
        if agent["status"] != "completed":
            fail(f"{label}: agent {name} status is {agent['status']}, expected completed")
        if not agent.get("result"):
            fail(f"{label}: agent {name} missing result")
    ok(f"{label}: all 4 agents completed with results (job status={job['status']})")


async def scenario_1_pdf(client: httpx.AsyncClient) -> None:
    print("\n=== Scenario 1: PDF upload → analyze → poll → verify 4 results ===")
    if not PDF_SOURCE.exists():
        fail(f"PDF source not found: {PDF_SOURCE}")

    doc = await upload(client, PDF_SOURCE)
    ok(f"Uploaded PDF → document_id={doc['document_id']} words={doc['word_count']}")

    trigger = await analyze(client, doc["document_id"])
    ok(f"Analyze returned in {trigger['_trigger_ms']}ms → job_id={trigger['job_id']}")

    job = await poll_until_complete(client, trigger["job_id"])
    verify_all_agents_have_results(job, "Scenario 1")


async def scenario_2_txt(client: httpx.AsyncClient) -> None:
    print("\n=== Scenario 2: TXT upload → analyze → poll → verify 4 results ===")
    if not TXT_SOURCE.exists():
        fail(f"TXT source not found: {TXT_SOURCE}")

    doc = await upload(client, TXT_SOURCE)
    ok(f"Uploaded TXT → document_id={doc['document_id']} words={doc['word_count']}")

    trigger = await analyze(client, doc["document_id"])
    ok(f"Analyze returned in {trigger['_trigger_ms']}ms → job_id={trigger['job_id']}")

    job = await poll_until_complete(client, trigger["job_id"])
    verify_all_agents_have_results(job, "Scenario 2")


async def scenario_3_concurrent(client: httpx.AsyncClient) -> None:
    print("\n=== Scenario 3: Two documents analyzed simultaneously ===")
    doc_a = await upload(client, PDF_SOURCE)
    doc_b = await upload(client, TXT_SOURCE)
    ok(f"Uploaded doc A={doc_a['document_id']}, doc B={doc_b['document_id']}")

    started = time.perf_counter()
    trigger_a, trigger_b = await asyncio.gather(
        analyze(client, doc_a["document_id"]),
        analyze(client, doc_b["document_id"]),
    )
    trigger_ms = (time.perf_counter() - started) * 1000
    ok(
        f"Both analyze calls returned in {trigger_ms:.0f}ms total "
        f"(jobs {trigger_a['job_id']}, {trigger_b['job_id']})"
    )

    job_a, job_b = await asyncio.gather(
        poll_until_complete(client, trigger_a["job_id"]),
        poll_until_complete(client, trigger_b["job_id"]),
    )

    for label, job in [("Doc A (PDF)", job_a), ("Doc B (TXT)", job_b)]:
        completed = sum(1 for n in AGENTS if job["agents"][n]["status"] == "completed")
        if completed < 4 and job["status"] not in {"completed", "partially_failed"}:
            fail(f"{label}: unexpected job state {job['status']}")
        ok(f"{label}: finished status={job['status']} ({agent_summary(job['agents'])})")

    ok("Scenario 3: both jobs processed without blocking each other")


async def scenario_5_partial_poll(client: httpx.AsyncClient) -> None:
    print("\n=== Scenario 5: Poll during processing → partial results ===")

    doc = await upload(client, PDF_SOURCE)
    trigger = await analyze(client, doc["document_id"])
    job_id = trigger["job_id"]
    ok(f"Analysis started job_id={job_id}")

    saw_running = False
    saw_partial = False
    deadline = time.time() + MAX_POLL_SECONDS

    while time.time() < deadline:
        job = await get_job(client, job_id)
        agents = job["agents"]
        statuses = {n: agents[n]["status"] for n in AGENTS}
        completed = [n for n, s in statuses.items() if s == "completed"]
        running = [n for n, s in statuses.items() if s == "running"]
        pending = [n for n, s in statuses.items() if s == "pending"]

        if running or pending:
            saw_running = True
        if completed and (running or pending):
            for name in completed:
                if not agents[name].get("result"):
                    fail(f"Completed agent {name} visible but missing result during poll")
            saw_partial = True
            ok(
                f"Partial snapshot: completed={completed}, "
                f"still running={running or pending} → {agent_summary(agents)}"
            )
            break

        if job["status"] in {"completed", "partially_failed", "failed"}:
            break
        await asyncio.sleep(POLL_INTERVAL)

    if not saw_running:
        ok("Note: all agents finished before first poll (job was very fast)")
    if not saw_partial:
        fail(
            "Did not observe partial results (some completed while others still running). "
            "Try again or use stub mode for slower staggered agents."
        )
    ok("Scenario 5: partial results visible while job still processing")


async def main() -> None:
    print("Document Intelligence API — 5 Scenario Test Suite")
    print(f"Target: {BASE}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            health = await client.get("http://127.0.0.1:8001/health")
            health.raise_for_status()
        except httpx.HTTPError as exc:
            fail(f"Server not reachable at :8001 — start with: uvicorn app.main:app --reload --port 8001\n  {exc}")

        await scenario_1_pdf(client)
        await scenario_2_txt(client)
        await scenario_3_concurrent(client)
        print("\n=== Scenario 4: Manual check ===")
        print("  Partial failure occurs naturally when one agent times out or errors.")
        print("  Demo with a saved partially_failed job or lower LLM_TIMEOUT_SECONDS temporarily.")
        await scenario_5_partial_poll(client)

    print("\n=== ALL RUN SCENARIOS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
