from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from ..graph import Graph


class Extractor(ABC):
    """Language-agnostic extractor interface.

    Implementations inspect a single file's source code and add nodes/edges to the graph.
    They should be idempotent and safe to run multiple times.
    """

    @abstractmethod
    def supports(self, file_path: str, text: str) -> bool:
        """Return True if this extractor should run for the given file/text."""
        raise NotImplementedError

    @abstractmethod
    def extract(self, file_path: str, text: str, graph: Graph) -> None:
        """Analyze text of file_path and mutate graph with nodes and edges."""
        raise NotImplementedError

    def language_hint(self, file_path: str) -> Optional[str]:
        return None
