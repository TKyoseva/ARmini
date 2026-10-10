"""pytest setup: make tools/parts importable as top-level modules (like agent.py does) and
block the network — tests must run with no connection at all."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.dirname(HERE)
if PARTS not in sys.path:
    sys.path.insert(0, PARTS)

FIXTURES = os.path.join(HERE, "fixtures")
STARTER_NEEDS = os.path.join(PARTS, "..", "..", "parts", "needs.yaml")


def fixture(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any real HTTP call in a test is a bug."""
    import requests

    def boom(*a, **k):
        raise AssertionError("network access attempted in a test")

    monkeypatch.setattr(requests.Session, "request", boom)
    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(requests, "get", boom)
    yield
