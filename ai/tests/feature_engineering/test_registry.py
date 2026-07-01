"""Tests for FeatureRegistry and topological ordering."""

from __future__ import annotations

import pandas as pd
import pytest

from feature_engineering.base import BaseFeature
from feature_engineering.registry import FeatureRegistry, RegistryError

# ---------------------------------------------------------------------------
# Minimal stub feature for registry tests
# ---------------------------------------------------------------------------


class _StubFeature(BaseFeature):
    """Minimal BaseFeature implementation for registry tests."""

    def __init__(self, name_: str, deps: list[str] | None = None) -> None:
        self._name = name_
        self._deps = deps or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return self._deps

    @property
    def output_columns(self) -> list[str]:
        return [f"{self._name}_col"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(index=df.index)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_register_and_get_by_name() -> None:
    """A feature registered under its name is retrievable via get()."""
    registry = FeatureRegistry()
    feature = _StubFeature("alpha")
    registry.register(feature)
    assert registry.get("alpha") is feature


def test_register_duplicate_raises() -> None:
    """Registering two features with the same name raises RegistryError."""
    registry = FeatureRegistry()
    registry.register(_StubFeature("alpha"))
    with pytest.raises(RegistryError, match="already registered"):
        registry.register(_StubFeature("alpha"))


def test_get_unknown_raises() -> None:
    """Getting an unregistered name raises RegistryError."""
    registry = FeatureRegistry()
    with pytest.raises(RegistryError, match="not registered"):
        registry.get("nonexistent")


def test_get_ordered_no_dependencies() -> None:
    """With no deps, get_ordered() returns all registered features."""
    registry = FeatureRegistry()
    a = _StubFeature("a")
    b = _StubFeature("b")
    c = _StubFeature("c")
    for f in [a, b, c]:
        registry.register(f)
    ordered = registry.get_ordered()
    assert {f.name for f in ordered} == {"a", "b", "c"}
    assert len(ordered) == 3


def test_get_ordered_dependency_before_dependent() -> None:
    """When X depends on Y, Y must appear before X in the ordered list."""
    registry = FeatureRegistry()
    registry.register(_StubFeature("base"))
    registry.register(_StubFeature("derived", deps=["base"]))
    ordered = registry.get_ordered()
    names = [f.name for f in ordered]
    assert names.index("base") < names.index("derived")


def test_get_ordered_missing_dependency_raises() -> None:
    """A declared dependency that is not registered raises RegistryError."""
    registry = FeatureRegistry()
    registry.register(_StubFeature("derived", deps=["missing_dep"]))
    with pytest.raises(RegistryError, match="missing_dep"):
        registry.get_ordered()


def test_get_ordered_cycle_raises() -> None:
    """A cyclic dependency graph raises RegistryError."""
    registry = FeatureRegistry()
    registry.register(_StubFeature("x", deps=["y"]))
    registry.register(_StubFeature("y", deps=["x"]))
    with pytest.raises(RegistryError, match="[Cc]ycle"):
        registry.get_ordered()


def test_names_returns_all_registered() -> None:
    """names() returns the names of all registered features."""
    registry = FeatureRegistry()
    registry.register(_StubFeature("one"))
    registry.register(_StubFeature("two"))
    assert set(registry.names()) == {"one", "two"}
