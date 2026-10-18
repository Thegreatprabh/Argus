"""Tests for rebuild + setup_agents + firmware parse (offline)."""

import json
import tempfile
from pathlib import Path

from argus.engines.firmware import FirmwareEngine
from argus.engines.rebuild import RebuildEngine, _fn_name, _slug
from argus.setup_agents import plan


def test_slug():
    assert _slug("https://x.com/pricing?y=1") == "pricing"
    assert _slug("https://x.com/") == "index"


def test_fn_name():
    assert _fn_name("https://a.com/api/v1/auth/login") == "call_auth_login"
    assert _fn_name("/graphql") == "call_endpoint"


def test_rebuild_generates_files():
    eng = RebuildEngine()
    bp = {"kind": "web", "source": "https://example.com",
          "tech": ["Next.js"],
          "pages": [{"url": "https://example.com", "slug": "index"},
                    {"url": "https://example.com/pricing", "slug": "pricing"}],
          "endpoints": ["https://example.com/api/v1/login"],
          "forms": [], "findings": []}
    with tempfile.TemporaryDirectory() as d:
        files = eng.generate(bp, d, project="demo")
        assert "src/api.js" in files
        assert "index.html" in files
        assert "pages/pricing.html" in files
        assert "REBUILD_NOTES.md" in files
        api = Path(d, "src/api.js").read_text()
        assert "call_login" in api


def test_setup_plan_json():
    items = plan("cursor")
    assert len(items) == 1
    key, label, path, content = items[0]
    assert key == "cursor"
    assert content["mcpServers"]["argus"]["args"] == ["-m", "argus.mcp_server"]


def test_firmware_parse():
    eng = FirmwareEngine()
    sample = ("DECIMAL       HEXADECIMAL     DESCRIPTION\n"
              "0             0x0             JFFS2 filesystem\n"
              "128           0x80            gzip compressed data\n")
    sigs = eng._parse(sample)
    assert ("0", "JFFS2 filesystem") in sigs
    assert len(sigs) == 2
