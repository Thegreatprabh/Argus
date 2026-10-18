"""Tests for the web engine (offline — no network)."""

from argus.engines import web

SAMPLE_HTML = """
<html><head>
<meta name="generator" content="WordPress 6.4">
<script src="/static/app.js"></script>
<script src="https://www.googletagmanager.com/gtag/js?id=1"></script>
</head><body>
<div id="__NEXT_DATA__"></div>
<script>fetch('/api/v1/users'); axios.post("/api/v1/login")</script>
<form action="/submit"></form>
</body></html>
"""


def test_scripts_resolve_absolute():
    scripts = web._scripts(SAMPLE_HTML, "https://example.com/page")
    assert "https://example.com/static/app.js" in scripts
    assert "https://www.googletagmanager.com/gtag/js?id=1" in scripts


def test_tech_stack():
    tech = web._tech_stack(SAMPLE_HTML)
    assert "Next.js" in tech
    assert "WordPress" in tech


def test_trackers():
    scripts = web._scripts(SAMPLE_HTML, "https://example.com/")
    assert "googletagmanager.com" in web._trackers(scripts)


def test_endpoints():
    eps = web._endpoints([SAMPLE_HTML])
    assert "/api/v1/users" in eps
    assert "/api/v1/login" in eps


def test_forms():
    forms = web._forms(SAMPLE_HTML, "https://example.com/")
    assert forms == ["https://example.com/submit"]
