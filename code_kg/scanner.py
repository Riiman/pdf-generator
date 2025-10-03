from __future__ import annotations
import os
from typing import Iterable, List, Optional, Sequence

from .graph import Graph, NodeKind, EdgeKind
from .extractors.base import Extractor
from .extractors.heuristic import HeuristicExtractor


DEFAULT_IGNORES = {".git", "node_modules", ".venv", "__pycache__", ".idea", ".vscode", "dist", "build"}
DEFAULT_EXTENSIONS = None  # None means include all regular files


class Scanner:
    def __init__(self, extractors: Optional[Sequence[Extractor]] = None, extensions: Optional[Sequence[str]] = DEFAULT_EXTENSIONS, ignores: Optional[Sequence[str]] = None) -> None:
        self.extractors: List[Extractor] = list(extractors) if extractors else [HeuristicExtractor()]
        self.extensions: Optional[set[str]] = set(extensions) if extensions is not None else None
        self.ignores: set[str] = set(ignores or DEFAULT_IGNORES)

    def should_include_file(self, path: str) -> bool:
        base = os.path.basename(path)
        if base.startswith('.'):
            return False
        if any(part in self.ignores for part in path.split(os.sep)):
            return False
        if self.extensions is not None:
            _, ext = os.path.splitext(base)
            return ext.lower() in self.extensions
        return os.path.isfile(path)

    def walk_paths(self, paths: Sequence[str]) -> Iterable[str]:
        for root_path in paths:
            if os.path.isfile(root_path):
                if self.should_include_file(root_path):
                    yield root_path
                continue
            for dirpath, dirnames, filenames in os.walk(root_path):
                dirnames[:] = [d for d in dirnames if d not in self.ignores and not d.startswith('.')]
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    if self.should_include_file(full_path):
                        yield full_path

    def scan(self, paths: Sequence[str]) -> Graph:
        graph = Graph()
        for file_path in self.walk_paths(paths):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read()
            except Exception:
                # Binary or unreadable file
                continue

            for extractor in self.extractors:
                try:
                    if extractor.supports(file_path, text):
                        extractor.extract(file_path, text, graph)
                except Exception:
                    # Best-effort scanning; skip extractor errors per file
                    continue
        return graph
