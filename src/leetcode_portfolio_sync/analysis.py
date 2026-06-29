from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from typing import TypedDict

from .models import CodeAnalysis


class AnalysisSignals(TypedDict):
    algorithms: list[str]
    data_structures: list[str]
    patterns: list[str]
    graph: bool
    dp: bool
    greedy: bool
    sliding_window: bool


class CodeAnalyzer:
    def analyze(self, code: str, language: str) -> CodeAnalysis:
        if language in {"Python", "Python3"}:
            return PythonAstAnalyzer().analyze(code, language)
        return HeuristicAnalyzer().analyze(code, language)


class PythonAstAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.functions: set[str] = set()
        self.calls: set[str] = set()
        self.assignments: set[str] = set()
        self.loop_count = 0
        self.branch_count = 0
        self.max_loop_depth = 0
        self._loop_depth = 0

    def analyze(self, code: str, language: str) -> CodeAnalysis:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return HeuristicAnalyzer().analyze(code, language)
        self.visit(tree)
        signals = extract_signals(code, self.calls | self.assignments)
        return CodeAnalysis(
            language=language,
            algorithms=signals["algorithms"],
            data_structures=signals["data_structures"],
            patterns=signals["patterns"],
            uses_recursion=bool(self.functions & self.calls),
            uses_graph_traversal=signals["graph"],
            uses_dynamic_programming=signals["dp"],
            uses_greedy=signals["greedy"],
            uses_sliding_window=signals["sliding_window"],
            loop_count=self.loop_count,
            branch_count=self.branch_count,
            function_count=len(self.functions),
            max_loop_depth=self.max_loop_depth,
            time_complexity=estimate_time_complexity(
                self.loop_count,
                self.max_loop_depth,
                signals["dp"],
                signals["graph"],
            ),
            space_complexity=estimate_space_complexity(signals["data_structures"]),
            explanation=build_analysis_explanation(signals["patterns"]),
            mermaid=build_mermaid(signals["patterns"]),
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.assignments.update(names(target))
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._enter_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._enter_loop(node)

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def _enter_loop(self, node: ast.AST) -> None:
        self.loop_count += 1
        self._loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self._loop_depth)
        self.generic_visit(node)
        self._loop_depth -= 1


class HeuristicAnalyzer:
    def analyze(self, code: str, language: str) -> CodeAnalysis:
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code))
        signals = extract_signals(code, tokens)
        loop_count = len(re.findall(r"\b(for|while)\b", code))
        branch_count = len(re.findall(r"\b(if|else if|switch|when)\b", code))
        return CodeAnalysis(
            language=language,
            algorithms=signals["algorithms"],
            data_structures=signals["data_structures"],
            patterns=signals["patterns"],
            uses_recursion=detect_non_python_recursion(code),
            uses_graph_traversal=signals["graph"],
            uses_dynamic_programming=signals["dp"],
            uses_greedy=signals["greedy"],
            uses_sliding_window=signals["sliding_window"],
            loop_count=loop_count,
            branch_count=branch_count,
            function_count=len(
                re.findall(r"\b(function|def|func|fn|public|private)\b", code)
            ),
            max_loop_depth=(
                2
                if re.search(r"\bfor\b.*\bfor\b", code, re.DOTALL)
                else min(loop_count, 1)
            ),
            time_complexity=estimate_time_complexity(
                loop_count, min(loop_count, 2), signals["dp"], signals["graph"]
            ),
            space_complexity=estimate_space_complexity(signals["data_structures"]),
            explanation=build_analysis_explanation(signals["patterns"]),
            mermaid=build_mermaid(signals["patterns"]),
        )


def names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        return {name for child in node.elts for name in names(child)}
    if isinstance(node, ast.Attribute):
        return {node.attr}
    return set()


def extract_signals(code: str, tokens: Iterable[str]) -> AnalysisSignals:
    lowered = code.lower()
    token_set = {token.lower() for token in tokens}
    data_structures: set[str] = set()
    algorithms: set[str] = set()
    patterns: set[str] = set()
    if token_set & {"dict", "defaultdict", "counter", "hashmap", "map", "set"}:
        data_structures.update({"Hash Map", "Set"})
    if token_set & {"deque", "queue"}:
        data_structures.add("Queue")
    if token_set & {"heapq", "priorityqueue", "heap"}:
        data_structures.add("Heap")
        algorithms.add("Priority Queue")
    if token_set & {"stack"}:
        data_structures.add("Stack")
    if token_set & {"left", "right", "window", "l", "r"}:
        patterns.add("Two Pointers")
    graph = bool(token_set & {"dfs", "bfs", "visited", "adj", "graph", "neighbors"})
    dp = bool(token_set & {"dp", "memo", "cache"} or "memoization" in lowered)
    greedy = bool(token_set & {"greedy", "maxprofit", "mincost"} or "sort(" in lowered)
    sliding = bool(
        token_set & {"window", "left", "right"}
        and re.search(r"\bwhile\b.*left", lowered, re.DOTALL)
    )
    if graph:
        algorithms.add("Graph Traversal")
        patterns.add("Graph")
    if dp:
        algorithms.add("Dynamic Programming")
        patterns.add("Dynamic Programming")
    if greedy:
        algorithms.add("Greedy")
        patterns.add("Greedy")
    if sliding:
        algorithms.add("Sliding Window")
        patterns.add("Sliding Window")
    if not algorithms:
        algorithms.add("Implementation")
    if not data_structures:
        data_structures.add("Array")
    if not patterns:
        patterns.add("Implementation")
    return {
        "algorithms": sorted(algorithms),
        "data_structures": sorted(data_structures),
        "patterns": sorted(patterns),
        "graph": graph,
        "dp": dp,
        "greedy": greedy,
        "sliding_window": sliding,
    }


def estimate_time_complexity(loop_count: int, depth: int, dp: bool, graph: bool) -> str:
    if graph:
        return "O(V + E)"
    if dp:
        return "O(n * states)"
    if depth >= 2:
        return "O(n^2)"
    if loop_count >= 1:
        return "O(n)"
    return "O(1)"


def estimate_space_complexity(data_structures: list[str]) -> str:
    if any(
        name in data_structures
        for name in ["Hash Map", "Set", "Queue", "Heap", "Stack"]
    ):
        return "O(n)"
    return "O(1)"


def build_analysis_explanation(patterns: list[str]) -> str:
    return "The submitted implementation primarily uses " + ", ".join(patterns) + "."


def build_mermaid(patterns: list[str]) -> str:
    label = " / ".join(patterns)
    return f"""```mermaid
flowchart TD
    A[Read input] --> B[Apply {label}]
    B --> C[Update state]
    C --> D[Return answer]
```"""


def detect_non_python_recursion(code: str) -> bool:
    names_found = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[{=]", code)
    return any(len(re.findall(rf"\b{name}\s*\(", code)) > 1 for name in names_found)
