from __future__ import annotations

import argparse
import asyncio
import json

from backend.app.db.init import init_db
from backend.app.db.session import SessionLocal
from backend.app.services.embeddings import build_embedding_client
from backend.app.services.reindex import DEFAULT_REINDEX_BATCH_SIZE, run_reindex


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


async def reindex_command(args: argparse.Namespace) -> None:
    await init_db()
    async with SessionLocal() as session:
        result = await run_reindex(
            session,
            build_embedding_client(),
            dry_run=args.dry_run,
            source_ids=args.source_id,
            categories=args.category,
            batch_size=args.batch_size,
            resume_run_id=args.resume_run_id,
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


def reindex_main() -> None:
    parser = argparse.ArgumentParser(description="Reindex Knowledge Hub embeddings.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates and persist a dry-run record without mutating embeddings.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Restrict reindexation to a source public id. Can be repeated.",
    )
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="Restrict reindexation to a category name. Can be repeated.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=DEFAULT_REINDEX_BATCH_SIZE,
        help=f"Maximum chunks to execute in this slice. Default: {DEFAULT_REINDEX_BATCH_SIZE}.",
    )
    parser.add_argument(
        "--resume-run-id",
        help="Resume pending or retryable items from a previous run public id.",
    )
    args = parser.parse_args()
    asyncio.run(reindex_command(args))


if __name__ == "__main__":
    reindex_main()
