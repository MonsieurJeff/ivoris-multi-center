"""
CLI for Ivoris Multi-Center Extraction Pipeline.

Workflow:
1. generate_test_dbs.py    - Create databases with random schemas
2. discover-raw            - View raw schema from database
3. generate-mappings       - Create mapping files (for manual review)
4. extract                 - Extract data using mappings
5. benchmark               - Performance test
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from ..core.config import load_config
from ..core.introspector import clear_cache, list_available_mappings
from ..services.extraction import ExtractionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Directories
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MAPPINGS_DIR = DATA_DIR / "mappings"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"


def cmd_discover_raw(args, config):
    """Discover and display RAW schemas from databases."""
    from ..core.discovery import SchemaDiscovery

    centers = config.centers
    if args.center:
        centers = [c for c in centers if c.id == args.center]
        if not centers:
            logger.error(f"Unknown center: {args.center}")
            return 1

    for center in centers:
        conn_str = config.database.connection_string(center.database)

        try:
            discovery = SchemaDiscovery(conn_str)
            discovered = discovery.discover()

            print(f"\n{'='*60}")
            print(f"Center: {center.name} ({center.id})")
            print(f"Database: {discovered.database}")
            print(f"{'='*60}")

            for table in discovered.tables:
                print(f"\nTABLE: {table.schema}.{table.name}")
                for col in table.columns:
                    nullable = "NULL" if col.is_nullable else "NOT NULL"
                    print(f"  - {col.name} ({col.data_type}, {nullable})")

        except Exception as e:
            print(f"\n{center.name}: Error - {e}")

    return 0


def cmd_generate_mappings(args, config):
    """Generate mapping files from discovered schemas."""
    from ..services.mapping_generator import generate_all_mappings

    logger.info("Generating mapping files from discovered schemas...")
    logger.info(f"Output directory: {MAPPINGS_DIR}")

    generated = generate_all_mappings(config, MAPPINGS_DIR)

    print(f"\n{'='*60}")
    print(f"Generated {len(generated)} mapping files")
    print(f"{'='*60}")
    print(f"\nFiles saved to: {MAPPINGS_DIR}")
    print("\nIMPORTANT: Review and adjust mappings as needed before extraction.")
    print("Each file has 'reviewed: false' flag - set to true after review.")

    return 0


def cmd_show_mapping(args, config):
    """Show a mapping file for a center."""
    import json

    if not args.center:
        # List available mappings
        available = list_available_mappings(MAPPINGS_DIR)
        if available:
            print("Available mappings:")
            for m in sorted(available):
                print(f"  - {m}")
        else:
            print("No mapping files found. Run 'generate-mappings' first.")
        return 0

    filepath = MAPPINGS_DIR / f"{args.center}_mapping.json"
    if not filepath.exists():
        logger.error(f"No mapping file for {args.center}")
        return 1

    with open(filepath) as f:
        mapping = json.load(f)

    print(f"\n{'='*60}")
    print(f"Mapping: {args.center}")
    print(f"Database: {mapping.get('database')}")
    print(f"Reviewed: {mapping.get('reviewed', False)}")
    print(f"{'='*60}")

    for canonical, table in mapping.get("tables", {}).items():
        print(f"\n{canonical} -> {table['actual_name']}")
        for col_canonical, col_data in table.get("columns", {}).items():
            print(f"  {col_canonical} -> {col_data['actual_name']}")

    unmapped = mapping.get("unmapped_tables", [])
    if unmapped:
        print(f"\nUnmapped tables: {', '.join(unmapped)}")

    return 0


def cmd_extract(args, config):
    """Extract chart entries from centers."""
    # Check for mapping files
    available = list_available_mappings(MAPPINGS_DIR)
    if not available:
        logger.error("No mapping files found.")
        logger.info("Run 'python -m src.cli generate-mappings' first.")
        return 1

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
    # Check for mapping files
    available = list_available_mappings(MAPPINGS_DIR)
    if not available:
        logger.error("No mapping files found.")
        logger.info("Run 'python -m src.cli generate-mappings' first.")
        return 1

    logger.info("Running benchmark...")

    # Clear cache to measure full load time
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

    # Check which have mappings
    available_mappings = set(list_available_mappings(MAPPINGS_DIR))

    for center in config.centers:
        has_mapping = center.id in available_mappings
        status = "[mapped]" if has_mapping else "[no mapping]"
        print(f"\n  {center.id} {status}")
        print(f"    Name: {center.name}")
        print(f"    City: {center.city}")
        print(f"    Database: {center.database}")

    print(f"\n{'='*60}")
    print(f"Total: {len(config.centers)} centers")
    print(f"Mapped: {len(available_mappings)} centers")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Ivoris Multi-Center Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. scripts/generate_test_dbs.py  - Create test databases
  2. discover-raw                  - View raw database schema
  3. generate-mappings             - Create mapping files
  4. show-mapping                  - Review a mapping file
  5. extract                       - Extract data
  6. benchmark                     - Performance test
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # discover-raw command
    discover_parser = subparsers.add_parser(
        "discover-raw", help="Discover RAW schema from database"
    )
    discover_parser.add_argument(
        "--center", "-c", help="Specific center ID (default: all)"
    )

    # generate-mappings command
    gen_parser = subparsers.add_parser(
        "generate-mappings", help="Generate mapping files from schemas"
    )

    # show-mapping command
    show_parser = subparsers.add_parser(
        "show-mapping", help="Show mapping file for a center"
    )
    show_parser.add_argument(
        "center", nargs="?", help="Center ID (omit to list available)"
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
        "discover-raw": cmd_discover_raw,
        "generate-mappings": cmd_generate_mappings,
        "show-mapping": cmd_show_mapping,
        "extract": cmd_extract,
        "benchmark": cmd_benchmark,
        "list": cmd_list,
    }

    return commands[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
