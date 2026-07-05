"""Regression test for the 2026-07-05 outage: SPA fallback returned None.

Commit d56a76e moved serve_frontend to the end of droplet_api.py but dropped
the final `return send_from_directory(FRONTEND_DIST, 'index.html')`. Every
page route then returned None -> Flask 500 -> site down. These tests fail on
that broken revision and pass with the fallback restored.
"""
import os

os.environ.setdefault("DAANAA_SKIP_EMBEDDINGS", "1")

import pytest

import droplet_api


@pytest.fixture()
def client():
    droplet_api.app.config["TESTING"] = True
    with droplet_api.app.test_client() as c:
        yield c


def test_root_serves_index(client):
    resp = client.get("/")
    assert resp.status_code == 200, f"/ returned {resp.status_code}, not the SPA"
    assert b"<!doctype html" in resp.data.lower()


def test_spa_route_falls_back_to_index(client):
    resp = client.get("/directory")
    assert resp.status_code == 200
    assert b"<!doctype html" in resp.data.lower()
