from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from backend.app.db.session import SessionLocal
from backend.app.services.embeddings import build_embedding_client
from backend.app.services.evaluation import (
    compare_reports,
    load_dataset,
    load_thresholds,
    read_report,
    run_evaluation,
    summarize_report,
    write_report,
)
from backend.app.services.rag import build_answer_client


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def probability(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between zero and one")
    return parsed


async def run_command(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.command == "summarize":
        return summarize_report(read_report(args.report)), 0
    if args.command == "compare":
        comparison = compare_reports(
            read_report(args.baseline),
            read_report(args.candidate),
            load_thresholds(args.thresholds),
        )
        write_report(args.output, comparison)
        return comparison, 0 if comparison["decision"] == "passed" else 1

    dataset, digest = load_dataset(args.dataset)
    thresholds = load_thresholds(args.thresholds)
    async with SessionLocal() as session:
        report = await run_evaluation(
            dataset,
            digest,
            thresholds,
            mode=args.command,
            session=session,
            embedding_client=build_embedding_client(),
            answer_client=None if args.search_only else build_answer_client(),
            search_only=args.search_only,
            limit=args.limit,
            min_score=args.min_score,
        )
    write_report(args.output, report)
    return report.model_dump(mode="json"), 0 if report.decision == "passed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate Knowledge Hub RAG quality from a versioned dataset."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("baseline", "candidate"):
        runner = subparsers.add_parser(command, help=f"Run a {command} RAG evaluation.")
        runner.add_argument("--dataset", type=Path, required=True)
        runner.add_argument("--thresholds", type=Path)
        runner.add_argument("--output", type=Path, required=True)
        runner.add_argument("--search-only", action="store_true")
        runner.add_argument("--limit", type=positive_int)
        runner.add_argument("--min-score", type=probability)
    compare = subparsers.add_parser(
        "compare", help="Compare a candidate report with a baseline report."
    )
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--thresholds", type=Path)
    compare.add_argument("--output", type=Path, required=True)
    summarize = subparsers.add_parser(
        "summarize", help="Print a compact evaluation report summary."
    )
    summarize.add_argument("--report", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        result, exit_code = asyncio.run(run_command(args))
    except (OSError, ValueError) as exc:
        print(f"rag-eval: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
