"""Parse the JavaScript embedded in every served HTML page and fail on a syntax error.

Why this exists: the app is a single Python file whose UI is large inline JS inside Python
triple-quoted strings. `ast.parse` only proves the *Python* is valid — it cannot see a broken
*JavaScript* string. Twice this bit us: a `\\'`-escaped quote inside a `\"\"\"` string is collapsed
by Python before the browser sees it (`onclick=\"f(\\'x\\')\"` -> `onclick=\"f('x')\"`), producing a
JS syntax error that kills the whole <script> block (dead send button, Enter no longer sends).

This test extracts each inline (non-src) <script> from every module-level `*_HTML` constant and
parses it with esprima, so that class of bug fails CI instead of the live site. Run:
    python -m pytest tests/test_inline_js_syntax.py
"""
import os
import re
import sys

import pytest

# Importing the app captures auth config (APP_PASSWORD / SESSION_SECRET) into module globals at
# import time, and pytest imports this module during collection — possibly before
# tests/test_report_api.py's fixture sets those env vars. Set the same canonical test credentials
# here first so the first importer (whichever it is) configures auth consistently; otherwise the
# API tests' login would fail purely because of test-collection order.
os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"

esprima = pytest.importorskip("esprima", reason="esprima not installed (pip install -r requirements-dev.txt)")

sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402

_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.DOTALL)


def _html_constant_names():
    """Names of module-level UPPER_HTML strings that contain an inline script.

    Parametrize on the *name* only (not the multi-KB HTML body) so the pytest node id
    stays short — on Windows the body would overflow the PYTEST_CURRENT_TEST env var.
    """
    names = [
        n for n in dir(app)
        if n.endswith("_HTML") and isinstance(getattr(app, n), str) and "<script" in getattr(app, n)
    ]
    assert names, "no *_HTML page constants with inline scripts were found"
    return names


@pytest.mark.parametrize("name", _html_constant_names())
def test_inline_js_parses(name):
    html = getattr(app, name)
    scripts = [s for s in _SCRIPT_RE.findall(html) if s.strip()]
    assert scripts, f"{name} has a <script> tag but no inline body to check"
    for i, body in enumerate(scripts):
        try:
            esprima.parseScript(body)
        except Exception as e:  # esprima raises esprima.Error; keep broad so the message surfaces
            pytest.fail(f"{name} inline <script> #{i} has a JavaScript syntax error: {e}")


def test_guard_actually_rejects_the_escape_collapse_bug():
    # Sanity: the exact pattern that twice slipped past ast.parse must be caught here, so a
    # green run means something. This is the browser-visible result of Python collapsing \\'.
    broken = "x.innerHTML = list.map(function(c){ return '<div onclick=\"go('' + c.id + '')\">'; });"
    with pytest.raises(Exception):
        esprima.parseScript(broken)
