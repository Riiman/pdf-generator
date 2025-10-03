from __future__ import annotations
import os
import re
from typing import Iterable, List, Tuple

from ..graph import Graph, NodeKind, EdgeKind
from .base import Extractor


class HeuristicExtractor(Extractor):
    """Framework- and language-agnostic heuristics using regex and simple rules.

    Recognizes:
    - files as nodes
    - import/include/use statements -> IMPORTS edges
    - function-like definitions -> FUNCTION/METHOD nodes and CALLS edges
    - class-like definitions -> CLASS nodes and EXTENDS/IMPLEMENTS edges
    - variable/const assignments -> VARIABLE/CONSTANT nodes
    - URLs or paths -> RESOURCE nodes; READS/WRITES heuristics via verbs
    """

    # Patterns are language-agnostic best-effort; not perfect by design
    IMPORT_PATTERNS = [
        re.compile(r"^\s*(?:import|from|using|use|include|require)\b(.+)$", re.IGNORECASE),
    ]

    FUNCTION_DEF_PATTERNS = [
        re.compile(r"^\s*(?:def|function|fn|proc|sub|lambda|async\s+function)\s+([A-Za-z_][\w]*)\b"),
        re.compile(r"^\s*([A-Za-z_][\w]*)\s*\([^)]*\)\s*\{?\s*$"),
    ]

    CLASS_DEF_PATTERNS = [
        re.compile(r"^\s*(?:class|struct|interface|trait)\s+([A-Za-z_][\w]*)"),
    ]

    EXTENDS_PATTERN = re.compile(r"\b(?:extends|implements|:|with)\s+([A-Za-z_][\w]*)")

    CONST_PATTERNS = [
        re.compile(r"^\s*(?:const|constexpr|final|immutable)\s+([A-Za-z_][\w]*)\b"),
    ]

    VAR_PATTERNS = [
        re.compile(r"^\s*(?:var|let|mut|auto|int|float|str|bool|char|double|long|short)\s+([A-Za-z_][\w]*)\b"),
    ]

    CALL_PATTERN = re.compile(r"\b([A-Za-z_][\w]*)\s*\(")

    # Use triple-quoted raw string to avoid quote-escaping issues
    RESOURCE_PATTERN = re.compile(r'''\b(https?://[^\s'")]+|/[^\s'")]+)\b''')

    WRITE_VERBS = {"write", "save", "put", "append", "update", "post"}
    READ_VERBS = {"read", "get", "open", "fetch", "load", "download"}

    def supports(self, file_path: str, text: str) -> bool:
        return True  # run for any text

    def extract(self, file_path: str, text: str, graph: Graph) -> None:
        file_id = Graph.node_id_for_file(file_path)
        graph.ensure_node(file_id, os.path.basename(file_path), NodeKind.FILE, {"path": file_path})

        lines = text.splitlines()
        # Imports
        for line in lines:
            for pat in self.IMPORT_PATTERNS:
                m = pat.match(line)
                if m:
                    target_raw = m.group(1).strip().strip(";{}()")
                    target = target_raw.split()[0]
                    imported_id = f"import:{target}"
                    graph.ensure_node(imported_id, target, NodeKind.MODULE)
                    graph.connect(file_id, imported_id, EdgeKind.IMPORTS, {"text": line.strip()})
                    break

        # Class and function definitions
        for idx, line in enumerate(lines, start=1):
            class_match = None
            for pat in self.CLASS_DEF_PATTERNS:
                class_match = pat.match(line)
                if class_match:
                    break
            if class_match:
                class_name = class_match.group(1)
                class_id = Graph.node_id_for_symbol(file_path, class_name)
                graph.ensure_node(class_id, class_name, NodeKind.CLASS, {"line": str(idx), "file": file_path})
                # extends/implements after name
                ext = self.EXTENDS_PATTERN.search(line)
                if ext:
                    base = ext.group(1)
                    base_id = f"type:{base}"
                    graph.ensure_node(base_id, base, NodeKind.TYPE)
                    graph.connect(class_id, base_id, EdgeKind.EXTENDS, {"line": str(idx)})
                continue

            func_match = None
            for pat in self.FUNCTION_DEF_PATTERNS:
                func_match = pat.match(line)
                if func_match:
                    break
            if func_match:
                func_name = func_match.group(1)
                func_id = Graph.node_id_for_symbol(file_path, func_name)
                graph.ensure_node(func_id, func_name, NodeKind.FUNCTION, {"line": str(idx), "file": file_path})
                graph.connect(file_id, func_id, EdgeKind.CONTAINS)

        # Variables and constants
        for idx, line in enumerate(lines, start=1):
            for pat in self.CONST_PATTERNS:
                m = pat.match(line)
                if m:
                    const_name = m.group(1)
                    const_id = Graph.node_id_for_symbol(file_path, const_name)
                    graph.ensure_node(const_id, const_name, NodeKind.CONSTANT, {"line": str(idx), "file": file_path})
                    graph.connect(file_id, const_id, EdgeKind.CONTAINS)
                    break
            for pat in self.VAR_PATTERNS:
                m = pat.match(line)
                if m:
                    var_name = m.group(1)
                    var_id = Graph.node_id_for_symbol(file_path, var_name)
                    graph.ensure_node(var_id, var_name, NodeKind.VARIABLE, {"line": str(idx), "file": file_path})
                    graph.connect(file_id, var_id, EdgeKind.CONTAINS)
                    break

        # Calls and resources
        for idx, line in enumerate(lines, start=1):
            for m in self.CALL_PATTERN.finditer(line):
                callee = m.group(1)
                callee_id = f"symbol:any:{callee}"
                graph.ensure_node(callee_id, callee, NodeKind.FUNCTION)
                graph.connect(file_id, callee_id, EdgeKind.CALLS, {"line": str(idx)})

            for res in self.RESOURCE_PATTERN.finditer(line):
                resource = res.group(1)
                resource_id = f"resource:{resource}"
                graph.ensure_node(resource_id, resource, NodeKind.RESOURCE)
                verb = line.strip().split("(")[0].split()[:1]
                verb = verb[0].lower() if verb else ""
                if verb in self.WRITE_VERBS:
                    graph.connect(file_id, resource_id, EdgeKind.WRITES, {"line": str(idx)})
                elif verb in self.READ_VERBS:
                    graph.connect(file_id, resource_id, EdgeKind.READS, {"line": str(idx)})
