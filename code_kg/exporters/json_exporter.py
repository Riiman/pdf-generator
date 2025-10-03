from __future__ import annotations
import json
from typing import Any

from ..graph import Graph


def export_json(graph: Graph, fp) -> None:
    data = graph.to_dict()
    json.dump(data, fp, indent=2, sort_keys=False)
