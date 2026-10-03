"""Connector contract and registry. See docs/SPEC.md §7."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

import httpx

from jobbot.models import RawJob


@runtime_checkable
class Source(Protocol):
    name: str

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]: ...


SourceFactory = Callable[[httpx.Client, dict[str, Any]], Source]

_REGISTRY: dict[str, SourceFactory] = {}


def register(name: str) -> Callable[[SourceFactory], SourceFactory]:
    def deco(factory: SourceFactory) -> SourceFactory:
        if name in _REGISTRY:
            raise ValueError(f"source {name!r} registered twice")
        _REGISTRY[name] = factory
        return factory

    return deco


def _discover() -> None:
    """Import every module in this package so @register decorators run."""
    for module in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{module.name}")


def available() -> dict[str, SourceFactory]:
    _discover()
    return dict(_REGISTRY)


def build(name: str, client: httpx.Client, params: dict[str, Any] | None = None) -> Source:
    factory = available().get(name)
    if factory is None:
        raise KeyError(f"unknown source {name!r}; known: {sorted(_REGISTRY)}")
    return factory(client, params or {})
