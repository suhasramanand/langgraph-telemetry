from __future__ import annotations

import pytest
from prometheus_client import CollectorRegistry


@pytest.fixture()
def registry() -> CollectorRegistry:
    return CollectorRegistry()
