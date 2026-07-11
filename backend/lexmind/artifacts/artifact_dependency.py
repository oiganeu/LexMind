"""Artifact dependency graph model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArtifactDependency:
    """A single directed dependency between two artifacts.

    ``parent_id`` produced ``child_id``.  The dependency direction
    follows the data-flow: the upstream artifact is the parent.
    """

    parent_id: str = ""
    child_id: str = ""
    relationship: str = "produced_by"
    pipeline_stage: str = ""


@dataclass
class DependencyGraph:
    """In-memory directed acyclic graph of artifact dependencies.

    Tracks parent-child relationships, allows traversal in both
    directions, and detects cycles.
    """

    _edges: dict[str, set[str]] = field(default_factory=dict)
    _reverse: dict[str, set[str]] = field(default_factory=dict)
    _metadata: dict[str, ArtifactDependency] = field(default_factory=dict)

    def add(self, dep: ArtifactDependency) -> None:
        """Add a dependency edge.  Raises on cycle detection."""
        if dep.parent_id == dep.child_id:
            raise ValueError("Self-dependency is not allowed")
        if self._would_create_cycle(dep.parent_id, dep.child_id):
            raise ValueError(
                f"Adding {dep.parent_id} -> {dep.child_id} would create a cycle"
            )
        self._edges.setdefault(dep.parent_id, set()).add(dep.child_id)
        self._reverse.setdefault(dep.child_id, set()).add(dep.parent_id)
        self._metadata[f"{dep.parent_id}->{dep.child_id}"] = dep

    def children(self, artifact_id: str) -> frozenset[str]:
        """Return IDs of artifacts that depend on *artifact_id*."""
        return frozenset(self._edges.get(artifact_id, set()))

    def parents(self, artifact_id: str) -> frozenset[str]:
        """Return IDs of artifacts that *artifact_id* depends on."""
        return frozenset(self._reverse.get(artifact_id, set()))

    def all_artifacts(self) -> frozenset[str]:
        """Return all artifact IDs that participate in any edge."""
        ids: set[str] = set()
        ids.update(self._edges.keys())
        ids.update(self._reverse.keys())
        return frozenset(ids)

    def roots(self) -> frozenset[str]:
        """Return artifact IDs with no parents (pipeline entry points)."""
        all_ids = self.all_artifacts()
        has_parent = set(self._reverse.keys())
        return frozenset(all_ids - has_parent)

    def leaves(self) -> frozenset[str]:
        """Return artifact IDs with no children (pipeline outputs)."""
        all_ids = self.all_artifacts()
        has_children = set(self._edges.keys())
        return frozenset(all_ids - has_children)

    def topological_order(self) -> list[str]:
        """Return a topological ordering of all artifact IDs."""
        in_degree: dict[str, int] = dict.fromkeys(self.all_artifacts(), 0)
        for children in self._edges.values():
            for child in children:
                in_degree[child] = in_degree.get(child, 0) + 1

        queue = [n for n, d in in_degree.items() if d == 0]
        result: list[str] = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for child in self._edges.get(node, set()):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(result) != len(in_degree):
            raise ValueError("Cycle detected in dependency graph")
        return result

    def _would_create_cycle(self, parent: str, child: str) -> bool:
        """Check if adding parent->child creates a cycle.

        A cycle exists if child can already reach parent through
        forward edges.
        """
        visited: set[str] = set()
        stack = [child]
        while stack:
            node = stack.pop()
            if node == parent:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(self._edges.get(node, set()))
        return False

    def remove(self, artifact_id: str) -> None:
        """Remove all edges involving *artifact_id*."""
        for child in self._edges.pop(artifact_id, set()):
            self._reverse.get(child, set()).discard(artifact_id)
        for parent in self._reverse.pop(artifact_id, set()):
            self._edges.get(parent, set()).discard(artifact_id)
        keys_to_remove = [
            k for k in self._metadata
            if k.startswith(artifact_id + "->") or k.endswith("->" + artifact_id)
        ]
        for k in keys_to_remove:
            del self._metadata[k]
