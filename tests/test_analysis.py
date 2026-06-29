from __future__ import annotations

from leetcode_portfolio_sync.analysis import CodeAnalyzer


def test_python_ast_analysis_detects_dynamic_programming() -> None:
    code = """
class Solution:
    def climbStairs(self, n: int) -> int:
        dp = [0] * (n + 1)
        dp[0] = 1
        dp[1] = 1
        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
        return dp[n]
"""

    analysis = CodeAnalyzer().analyze(code, "Python")

    assert analysis.uses_dynamic_programming is True
    assert "Dynamic Programming" in analysis.algorithms
    assert analysis.time_complexity == "O(n * states)"
    assert "mermaid" in analysis.mermaid


def test_python_ast_analysis_detects_graph_traversal_and_recursion() -> None:
    code = """
def dfs(node):
    if node in visited:
        return
    visited.add(node)
    for neighbor in graph[node]:
        dfs(neighbor)
"""

    analysis = CodeAnalyzer().analyze(code, "Python")

    assert analysis.uses_recursion is True
    assert analysis.uses_graph_traversal is True
    assert analysis.time_complexity == "O(V + E)"
