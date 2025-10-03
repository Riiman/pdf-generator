from __future__ import annotations
from typing import TextIO

from ..graph import Graph, EdgeKind


def escape(s: str) -> str:
    return s.replace("\"", "\\\"")


def export_dot(graph: Graph, fp: TextIO) -> None:
    fp.write("digraph code_kg {\n")
    fp.write("  rankdir=LR;\n")
    fp.write("  node [shape=box, style=rounded];\n")

    for n in graph.nodes():
        label = f"{n.name}\\n({n.kind.value})"
        fp.write(f"  \"{escape(n.id)}\" [label=\"{escape(label)}\"];\n")

    edge_styles = {
        EdgeKind.CONTAINS: "color=gray,style=dashed",
        EdgeKind.IMPORTS: "color=blue",
        EdgeKind.CALLS: "color=darkgreen",
        EdgeKind.EXTENDS: "color=purple",
        EdgeKind.IMPLEMENTS: "color=purple,style=dashed",
        EdgeKind.REFERENCES: "color=black,style=dotted",
        EdgeKind.READS: "color=orange",
        EdgeKind.WRITES: "color=red",
    }

    for e in graph.edges():
        style = edge_styles.get(e.kind, "")
        attrs = f" [label=\"{e.kind.value}\"" + ("," + style if style else "") + "]"
        fp.write(f"  \"{escape(e.source)}\" -> \"{escape(e.target)}\"{attrs};\n")

    fp.write("}\n")
