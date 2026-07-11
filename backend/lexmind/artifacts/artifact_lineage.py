"""Artifact lineage tracking model."""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmind.artifacts.artifact_dependency import DependencyGraph


@dataclass(frozen=True)
class LineageStep:
    """A single step in an artifact's lineage chain."""

    artifact_id: str = ""
    artifact_type: str = ""
    producer: str = ""
    checksum: str = ""


@dataclass
class LineageTracker:
    """Tracks the full provenance chain for artifacts.

    Wraps a :class:`DependencyGraph` and adds typed lineage
    traversal methods for audit and debugging.
    """

    graph: DependencyGraph = field(default_factory=DependencyGraph)

    def record_step(self, step: LineageStep) -> None:
        """Record that this artifact exists in the lineage."""
        pass

    def ancestors(self, artifact_id: str) -> list[str]:
        """Return all ancestor artifact IDs (breadth-first)."""
        visited: set[str] = set()
        result: list[str] = []
        queue = [artifact_id]
        while queue:
            node = queue.pop(0)
            for parent in self.graph.parents(node):
                if parent not in visited:
                    visited.add(parent)
                    result.append(parent)
                    queue.append(parent)
        return result

    def descendants(self, artifact_id: str) -> list[str]:
        """Return all descendant artifact IDs (breadth-first)."""
        visited: set[str] = set()
        result: list[str] = []
        queue = [artifact_id]
        while queue:
            node = queue.pop(0)
            for child in self.graph.children(node):
                if child not in visited:
                    visited.add(child)
                    result.append(child)
                    queue.append(child)
        return result

    def full_chain(self, artifact_id: str) -> list[str]:
        """Return the full lineage chain from root to *artifact_id*."""
        ancestors = self.ancestors(artifact_id)
        roots = [a for a in ancestors if not self.graph.parents(a)]
        if not roots:
            roots = [artifact_id]
        chain: list[str] = []
        for root in roots:
            order = self.graph.topological_order()
            root_idx = order.index(root) if root in order else 0
            for node in order[root_idx:]:
                if node not in chain:
                    chain.append(node)
        if artifact_id not in chain:
            chain.append(artifact_id)
        return chain

    def pipeline_stage(self, artifact_id: str) -> int:
        """Return the depth of *artifact_id* from the nearest root."""
        ancestors = self.ancestors(artifact_id)
        if not ancestors:
            return 0
        max_depth = 0
        for ancestor in ancestors:
            chain = self.full_chain(ancestor)
            if artifact_id in chain:
                depth = chain.index(artifact_id)
                max_depth = max(max_depth, depth)
        return max_depth
