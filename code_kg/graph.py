from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Iterable


class NodeKind(str, Enum):
    MODULE = "module"
    TYPE = "type"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    ENUM = "enum"
    PACKAGE = "package"
    FILE = "file"
    NAMESPACE = "namespace"
    RESOURCE = "resource"
    ENDPOINT = "endpoint"
    UNKNOWN = "unknown"


class EdgeKind(str, Enum):
    CONTAINS = "contains"          # A contains B (e.g., file contains class)
    DEFINES = "defines"            # A defines B (e.g., module defines function)
    CALLS = "calls"                # A calls B
    IMPORTS = "imports"            # A imports B
    EXTENDS = "extends"            # A extends B
    IMPLEMENTS = "implements"      # A implements B (interfaces/traits)
    REFERENCES = "references"      # A references B (variable/type use)
    RETURNS = "returns"            # function returns type
    PARAM = "param"                # function has parameter type
    THROWS = "throws"              # function may throw/raise type
    READS = "reads"                # reads resource/file
    WRITES = "writes"              # writes resource/file
    DECORATES = "decorates"        # decorated by / uses decorator
    OVERRIDES = "overrides"        # method overrides


@dataclass(eq=True, frozen=True)
class Node:
    id: str
    name: str
    kind: NodeKind
    meta: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    @staticmethod
    def from_meta(id: str, name: str, kind: NodeKind, meta: Optional[Dict[str, str]] = None) -> "Node":
        items: Tuple[Tuple[str, str], ...] = tuple(sorted((meta or {}).items()))
        return Node(id=id, name=name, kind=kind, meta=items)

    def meta_dict(self) -> Dict[str, str]:
        return dict(self.meta)


@dataclass(eq=True, frozen=True)
class Edge:
    source: str
    target: str
    kind: EdgeKind
    meta: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    @staticmethod
    def from_meta(source: str, target: str, kind: EdgeKind, meta: Optional[Dict[str, str]] = None) -> "Edge":
        items: Tuple[Tuple[str, str], ...] = tuple(sorted((meta or {}).items()))
        return Edge(source=source, target=target, kind=kind, meta=items)

    def meta_dict(self) -> Dict[str, str]:
        return dict(self.meta)


class Graph:
    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._out_edges: Dict[str, Set[Edge]] = {}
        self._in_edges: Dict[str, Set[Edge]] = {}

    # Nodes
    def upsert_node(self, node: Node) -> Node:
        self._nodes[node.id] = node
        self._out_edges.setdefault(node.id, set())
        self._in_edges.setdefault(node.id, set())
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def ensure_node(self, node_id: str, name: str, kind: NodeKind, meta: Optional[Dict[str, str]] = None) -> Node:
        if node_id in self._nodes:
            return self._nodes[node_id]
        node = Node.from_meta(node_id, name, kind, meta)
        return self.upsert_node(node)

    # Edges
    def add_edge(self, edge: Edge) -> Edge:
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise KeyError("Both source and target nodes must exist before adding an edge")
        self._out_edges[edge.source].add(edge)
        self._in_edges[edge.target].add(edge)
        return edge

    def connect(self, source_id: str, target_id: str, kind: EdgeKind, meta: Optional[Dict[str, str]] = None) -> Edge:
        edge = Edge.from_meta(source_id, target_id, kind, meta)
        return self.add_edge(edge)

    # Queries
    def nodes(self) -> Iterable[Node]:
        return self._nodes.values()

    def edges(self) -> Iterable[Edge]:
        for edges in self._out_edges.values():
            for e in edges:
                yield e

    def successors(self, node_id: str, kind: Optional[EdgeKind] = None) -> Iterable[Node]:
        for e in self._out_edges.get(node_id, set()):
            if kind is None or e.kind == kind:
                n = self._nodes.get(e.target)
                if n:
                    yield n

    def predecessors(self, node_id: str, kind: Optional[EdgeKind] = None) -> Iterable[Node]:
        for e in self._in_edges.get(node_id, set()):
            if kind is None or e.kind == kind:
                n = self._nodes.get(e.source)
                if n:
                    yield n

    # Export helpers
    def to_dict(self) -> Dict[str, List[Dict[str, object]]]:
        return {
            "nodes": [
                {"id": n.id, "name": n.name, "kind": n.kind.value, "meta": dict(n.meta)}
                for n in self.nodes()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "kind": e.kind.value,
                    "meta": dict(e.meta),
                }
                for e in self.edges()
            ],
        }

    def subgraph(self, node_ids: Set[str]) -> "Graph":
        sub = Graph()
        for node_id in node_ids:
            node = self._nodes.get(node_id)
            if node:
                sub.upsert_node(node)
        for e in self.edges():
            if e.source in node_ids and e.target in node_ids:
                sub.add_edge(e)
        return sub

    # Build utilities
    @staticmethod
    def node_id_for_file(path: str) -> str:
        return f"file:{path}"

    @staticmethod
    def node_id_for_symbol(file_path: str, symbol_name: str) -> str:
        return f"symbol:{file_path}:{symbol_name}"
