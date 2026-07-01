"""Feature registry with topological dependency ordering."""

from __future__ import annotations

from collections import deque

from feature_engineering.base import BaseFeature
from shared.exceptions import FootballAIError


class RegistryError(FootballAIError):
    """Raised for registry configuration problems (duplicates, cycles, missing deps)."""


class FeatureRegistry:
    """Stores feature instances and resolves their execution order."""

    def __init__(self) -> None:
        self._features: dict[str, BaseFeature] = {}

    def register(self, feature: BaseFeature) -> None:
        """Register a feature instance.

        Raises:
            RegistryError: If a feature with the same name is already registered.
        """
        if feature.name in self._features:
            raise RegistryError(
                f"Feature '{feature.name}' is already registered. "
                "Each feature name must be unique."
            )
        self._features[feature.name] = feature

    def get(self, name: str) -> BaseFeature:
        """Retrieve a feature by name.

        Raises:
            RegistryError: If no feature with that name is registered.
        """
        if name not in self._features:
            raise RegistryError(
                f"Feature '{name}' is not registered. "
                f"Available: {sorted(self._features)}"
            )
        return self._features[name]

    def names(self) -> list[str]:
        """Return all registered feature names (insertion order)."""
        return list(self._features.keys())

    def get_ordered(self) -> list[BaseFeature]:
        """Return features in dependency-safe topological order (Kahn's algorithm).

        Raises:
            RegistryError: If a declared dependency is not registered, or if the
                dependency graph contains a cycle.
        """
        # Validate all dependencies exist
        for feature in self._features.values():
            for dep in feature.dependencies:
                if dep not in self._features:
                    raise RegistryError(
                        f"Feature '{feature.name}' declares dependency '{dep}' "
                        "which is not registered."
                    )

        # Build in-degree map and adjacency list
        in_degree: dict[str, int] = dict.fromkeys(self._features, 0)
        dependents: dict[str, list[str]] = {name: [] for name in self._features}

        for feature in self._features.values():
            for dep in feature.dependencies:
                in_degree[feature.name] += 1
                dependents[dep].append(feature.name)

        # Kahn's algorithm
        queue: deque[str] = deque(
            name for name, degree in in_degree.items() if degree == 0
        )
        ordered: list[BaseFeature] = []

        while queue:
            name = queue.popleft()
            ordered.append(self._features[name])
            for dependent in dependents[name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(ordered) != len(self._features):
            remaining = [n for n, d in in_degree.items() if d > 0]
            raise RegistryError(
                f"Cycle detected in feature dependencies. "
                f"Features involved: {sorted(remaining)}"
            )

        return ordered
