"""Upload the generated test pack and exercise isolated and cross-document RAG."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

import httpx


BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = os.getenv("CONTEXTA_TEST_EMAIL", "portfolio.tester@contexta-demo.com")
TEST_PASSWORD = os.getenv("CONTEXTA_TEST_PASSWORD", "ContextaTest!2026")
TEST_NAME = os.getenv("CONTEXTA_TEST_NAME", "Contexta Portfolio Tester")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = PROJECT_ROOT / "examples" / "contexta-test-pack"
RESULT_PATH = PACK_DIR / "test_results.json"

CASES = [
    {
        "filename": "orion_product_knowledge.xlsx",
        "title": "Orion Product Knowledge",
        "question": "What is the warranty period for the Orbit Desk, and in which warehouse is it stored?",
        "expected_terms": ["3", "Basra"],
    },
    {
        "filename": "atlas_mission_brief.pdf",
        "title": "Mission Atlas Brief",
        "question": "When does Mission Atlas depart, and which instrument does it carry?",
        "expected_terms": ["14 March 2027", "AquaSpectra"],
    },
    {
        "filename": "cedar_support_policy.docx",
        "title": "Cedar Support Policy",
        "question": "How quickly must Priority Red tickets receive a response, and who manages escalations?",
        "expected_terms": ["15 minutes", "Omar Saleh"],
    },
    {
        "filename": "nova_architecture.md",
        "title": "Project Nova Architecture Notes",
        "question": "Which cache does Project Nova use, and what is its TTL?",
        "expected_terms": ["Redis", "12 minutes"],
    },
]


def require(response: httpx.Response, operation: str) -> httpx.Response:
    if response.is_error:
        raise RuntimeError(f"{operation} failed ({response.status_code}): {response.text[:800]}")
    return response


def matches(answer: str, terms: list[str]) -> bool:
    normalized = answer.casefold().replace("$", "")
    return all(term.casefold().replace("$", "") in normalized for term in terms)


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    report: dict[str, object] = {
        "base_url": base_url,
        "test_account": {"name": TEST_NAME, "email": TEST_EMAIL},
        "uploads": [],
        "individual_queries": [],
    }

    with httpx.Client(base_url=base_url, timeout=180.0, follow_redirects=True) as client:
        require(client.get("/health"), "health check")
        register = client.post(
            "/auth/register",
            json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        if register.status_code == 409:
            require(
                client.post(
                    "/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                ),
                "login",
            )
        else:
            require(register, "registration")

        existing = require(client.get("/documents"), "list documents").json()
        test_filenames = {
            f"{case['title']}{Path(case['filename']).suffix}" for case in CASES
        }
        for document in existing:
            if document["filename"] in test_filenames:
                require(client.delete(f"/documents/{document['id']}"), "remove prior test document")

        for case in CASES:
            path = PACK_DIR / case["filename"]
            with path.open("rb") as handle:
                response = require(
                    client.post(
                        "/documents/upload",
                        data={"title": case["title"]},
                        files={"file": (path.name, handle, "application/octet-stream")},
                    ),
                    f"upload {path.name}",
                )
            document = response.json()
            case["document_id"] = document["id"]
            report["uploads"].append(document)
            print(f"Uploaded {path.name}: {document['id']}", flush=True)

        for case in CASES:
            response = require(
                client.post(
                    "/query",
                    json={
                        "question": case["question"],
                        "document_id": case["document_id"],
                        "top_k": 6,
                    },
                ),
                f"query {case['filename']}",
            ).json()
            passed = matches(response["answer"], case["expected_terms"])
            report["individual_queries"].append(
                {
                    "filename": case["filename"],
                    "question": case["question"],
                    "expected_terms": case["expected_terms"],
                    "passed": passed,
                    **response,
                }
            )
            print(f"Individual {case['filename']}: {'PASS' if passed else 'FAIL'}", flush=True)

        combined_question = (
            "List the Mission Atlas departure date, the Orbit Desk unit price, "
            "the Priority Red response time, and Project Nova's cache TTL."
        )
        combined = require(
            client.post(
                "/query",
                json={"question": combined_question, "top_k": 20},
            ),
            "combined query",
        ).json()
        combined_terms = ["14 March 2027", "480", "15 minutes", "12 minutes"]
        report["all_documents_query"] = {
            "question": combined_question,
            "expected_terms": combined_terms,
            "passed": matches(combined["answer"], combined_terms),
            **combined,
        }

    report["passed"] = all(item["passed"] for item in report["individual_queries"]) and report[
        "all_documents_query"
    ]["passed"]
    report["completed_at_epoch"] = time.time()
    RESULT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
