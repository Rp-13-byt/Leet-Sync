from __future__ import annotations

from .models import ProblemMetadata, Recommendation

CURATED_RECOMMENDATIONS: dict[str, list[Recommendation]] = {
    "Array": [
        Recommendation(
            id=238,
            title="Product of Array Except Self",
            difficulty="Medium",
            reason="Practices prefix/suffix array reasoning.",
            url="https://leetcode.com/problems/product-of-array-except-self/",
        ),
        Recommendation(
            id=53,
            title="Maximum Subarray",
            difficulty="Medium",
            reason="Builds linear scan intuition.",
            url="https://leetcode.com/problems/maximum-subarray/",
        ),
    ],
    "Hash Table": [
        Recommendation(
            id=1,
            title="Two Sum",
            difficulty="Easy",
            reason="Canonical hash map lookup problem.",
            url="https://leetcode.com/problems/two-sum/",
        ),
        Recommendation(
            id=49,
            title="Group Anagrams",
            difficulty="Medium",
            reason="Uses keyed grouping with maps.",
            url="https://leetcode.com/problems/group-anagrams/",
        ),
    ],
    "Dynamic Programming": [
        Recommendation(
            id=70,
            title="Climbing Stairs",
            difficulty="Easy",
            reason="Introductory state transition problem.",
            url="https://leetcode.com/problems/climbing-stairs/",
        ),
        Recommendation(
            id=1143,
            title="Longest Common Subsequence",
            difficulty="Medium",
            reason="Classic 2D DP table.",
            url="https://leetcode.com/problems/longest-common-subsequence/",
        ),
    ],
    "Graph": [
        Recommendation(
            id=200,
            title="Number of Islands",
            difficulty="Medium",
            reason="Classic DFS/BFS grid traversal.",
            url="https://leetcode.com/problems/number-of-islands/",
        ),
        Recommendation(
            id=133,
            title="Clone Graph",
            difficulty="Medium",
            reason="Exercises visited maps and traversal.",
            url="https://leetcode.com/problems/clone-graph/",
        ),
    ],
    "Sliding Window": [
        Recommendation(
            id=3,
            title="Longest Substring Without Repeating Characters",
            difficulty="Medium",
            reason="Canonical variable-size window.",
            url="https://leetcode.com/problems/longest-substring-without-repeating-characters/",
        ),
    ],
}


class RecommendationEngine:
    def recommend(
        self, problem: ProblemMetadata, patterns: list[str]
    ) -> list[Recommendation]:
        seen: set[str] = {problem.title}
        output: list[Recommendation] = []
        for key in [*problem.tags, *patterns]:
            for recommendation in CURATED_RECOMMENDATIONS.get(key, []):
                if recommendation.title not in seen:
                    output.append(recommendation)
                    seen.add(recommendation.title)
                if len(output) >= 5:
                    return output
        return output or [
            Recommendation(
                title="Explore related tagged problems",
                reason="No curated match was available for the detected pattern.",
            )
        ]
