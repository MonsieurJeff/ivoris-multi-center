"""
CLI for Ivoris Multi-Center Extraction Pipeline.
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core.config import load_config
from ..core.introspector import clear_cache, get_schema
from ..services.extraction import ExtractionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def cmd_discover(args, config):
    """Discover and display schemas for all centers."""
    logger.info("Discovering schemas for all centers...")

    # Clear cache to force fresh discovery
    clear_cache()

    for center in config.centers:
        conn_str = config.database.connection_string(center.database)

        try:
            schema = get_schema(center.id, conn_str)
            print(f"\n{'='*60}")
            print(f"Center: {center.name} ({center.id})")
            print(f"Database: {center.database}")
            print(f"Schema Type: Random suffixes per table/column")
            print(f"{'='*60}")

            for table_name, table in schema.tables.items():
                print(f"\n  {table_name} -> {table.actual_name}")
                for canonical, col_mapping in table.columns.items():
                    if canonical != col_mapping.actual_name:
                        print(f"    {canonical} -> {col_mapping.actual_name}")
        except Exception as e:
            print(f"\n{center.name}: {e}")


def cmd_extract(args, config):
    """Extract chart entries from centers."""
    # Parse date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date: {args.date}. Use YYYY-MM-DD")
            return 1
    else:
        target_date = date.today() - timedelta(days=1)

    # Determine centers
    center_ids = None
    if args.center:
        center_ids = [args.center]
        if not config.get_center(args.center):
            logger.error(f"Unknown center: {args.center}")
            logger.info(f"Available: {', '.join(config.get_center_ids())}")
            return 1

    # Run extraction
    service = ExtractionService(config)
    result = service.extract_all(
        target_date=target_date,
        center_ids=center_ids,
        max_workers=args.workers,
    )

    # Output results
    print(f"\n{'='*60}")
    print(f"Extraction Complete")
    print(f"{'='*60}")
    print(f"Date: {result.target_date}")
    print(f"Centers: {result.successful_centers}/{len(result.results)}")
    print(f"Total Entries: {result.total_entries}")
    print(f"Total Time: {result.total_duration_ms:.0f}ms")
    print(f"{'='*60}")

    # Export
    if args.format in ("json", "both"):
        path = service.export_json(result)
        print(f"JSON: {path}")

    if args.format in ("csv", "both"):
        path = service.export_csv(result)
        print(f"CSV: {path}")

    return 0


def cmd_benchmark(args, config):
    """Run performance benchmark."""
    from datetime import date

    logger.info("Running benchmark...")

    # Clear schema cache to measure full introspection time
    clear_cache()

    service = ExtractionService(config)

    # Run extraction
    target_date = date(2022, 1, 18)  # Known test date
    result = service.extract_all(
        target_date=target_date,
        max_workers=args.workers,
    )

    # Report
    print(f"\n{'='*60}")
    print(f"BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Centers: {len(result.results)}")
    print(f"Total Entries: {result.total_entries}")
    print(f"Total Time: {result.total_duration_ms:.0f}ms")
    print(f"{'='*60}")
    print(f"\nPer-Center Timing:")

    for r in sorted(result.results, key=lambda x: x.duration_ms, reverse=True):
        status = "ok" if r.error is None else "err"
        print(
            f"  [{status}] {r.center_name:30} {r.duration_ms:6.0f}ms  ({len(r.entries)} entries)"
        )

    print(f"\n{'='*60}")
    target = 5000  # 5 seconds target
    if result.total_duration_ms < target:
        print(f"PASS: Under {target}ms target")
    else:
        print(f"FAIL: Over {target}ms target")
    print(f"{'='*60}")

    return 0


def cmd_list(args, config):
    """List all configured centers."""
    print(f"\n{'='*60}")
    print(f"Configured Dental Centers")
    print(f"{'='*60}")

    for center in config.centers:
        print(f"\n  {center.id}")
        print(f"    Name: {center.name}")
        print(f"    City: {center.city}")
        print(f"    Database: {center.database}")

    print(f"\n{'='*60}")
    print(f"Total: {len(config.centers)} centers")
    print(f"Note: Schema suffixes are random - use 'discover' to view")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Ivoris Multi-Center Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Discover schemas for all centers"
    )

    # extract command
    extract_parser = subparsers.add_parser("extract", help="Extract chart entries")
    extract_parser.add_argument(
        "--date", "-d", help="Target date (YYYY-MM-DD, default: yesterday)"
    )
    extract_parser.add_argument(
        "--center", "-c", help="Specific center ID (default: all)"
    )
    extract_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format",
    )
    extract_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=5,
        help="Max parallel workers (default: 5)",
    )

    # benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
    bench_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=5,
        help="Max parallel workers (default: 5)",
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List configured centers")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1

    # Dispatch command
    commands = {
        "discover": cmd_discover,
        "extract": cmd_extract,
        "benchmark": cmd_benchmark,
        "list": cmd_list,
    }

    return commands[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
