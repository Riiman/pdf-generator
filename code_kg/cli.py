from __future__ import annotations
import argparse
import sys
from pathlib import Path

from .scanner import Scanner
from .exporters.json_exporter import export_json
from .exporters.dot_exporter import export_dot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a language-agnostic knowledge graph from code")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--ext", action="append", help="Restrict to file extensions (e.g., --ext .py --ext .ts)")
    parser.add_argument("--format", choices=["json", "dot"], default="json", help="Output format")
    parser.add_argument("--out", type=str, help="Output file path (default: stdout)")
    args = parser.parse_args(argv)

    scanner = Scanner(extensions=args.ext)
    graph = scanner.scan(args.paths)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fp:
            if args.format == "json":
                export_json(graph, fp)
            else:
                export_dot(graph, fp)
    else:
        if args.format == "json":
            export_json(graph, sys.stdout)
        else:
            export_dot(graph, sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
