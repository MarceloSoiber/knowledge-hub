from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from backend.app.db.session import SessionLocal
from backend.app.services.embeddings import build_embedding_client
from backend.app.services.vector_index import (
    DEFAULT_MIN_CHUNKS,
    baseline_hnsw_index,
    create_hnsw_index,
    load_evaluation_queries,
    read_report,
    validate_hnsw_index,
    write_report,
)
from backend.app.repositories.vector_index import drop_hnsw_index, drop_hnsw_index_sql


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


async def run_command(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "drop":
        if not args.execute:
            return {"rollback_sql": drop_hnsw_index_sql(), "executed": False}
        async with SessionLocal() as session:
            await drop_hnsw_index(session)
            await session.commit()
        return {"rollback_sql": drop_hnsw_index_sql(concurrently=False), "executed": True}

    queries = load_evaluation_queries(args.queries, args.limit) if hasattr(args, "queries") else []
    async with SessionLocal() as session:
        if args.command == "baseline":
            report = await baseline_hnsw_index(session, build_embedding_client(), queries)
        elif args.command == "create":
            report = await create_hnsw_index(
                session, min_chunks=args.min_chunks, force=args.force
            )
            await session.commit()
        else:
            report = await validate_hnsw_index(
                session,
                build_embedding_client(),
                queries,
                read_report(args.baseline),
                recall_threshold=args.recall_threshold,
                hnsw_ef_search=args.hnsw_ef_search,
            )
        if args.output is not None:
            write_report(args.output, report)
        return report.to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate and validate the Knowledge Hub HNSW index.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline", help="Capture exact vector-search measurements.")
    baseline.add_argument("--queries", type=Path, required=True)
    baseline.add_argument("--limit", type=positive_int, default=10)
    baseline.add_argument("--output", type=Path, required=True)

    create = subparsers.add_parser("create", help="Create the HNSW index after preflight checks.")
    create.add_argument("--min-chunks", type=positive_int, default=DEFAULT_MIN_CHUNKS)
    create.add_argument("--force", action="store_true")
    create.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Compare HNSW results to an exact baseline.")
    validate.add_argument("--queries", type=Path, required=True)
    validate.add_argument("--baseline", type=Path, required=True)
    validate.add_argument("--limit", type=positive_int, default=10)
    validate.add_argument("--recall-threshold", type=probability, default=0.95)
    validate.add_argument("--hnsw-ef-search", type=positive_int)
    validate.add_argument("--output", type=Path, required=True)

    drop = subparsers.add_parser("drop", help="Print or execute the index rollback.")
    drop.add_argument("--execute", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = asyncio.run(run_command(args))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
