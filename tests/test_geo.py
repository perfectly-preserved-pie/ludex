"""Detect crawler regressions against the same local server used by browser tests."""

import json
import subprocess
import warnings
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from app import public_pages


pytestmark = pytest.mark.geo
ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PAGE_SIGNALS = ("js.server-rendered", "jsonld.present", "meta.complete")
REQUIRED_CHECKS = (
    "content.no-js",
    "trust.anchors",
    "nav.not-found",
    "nav.not-found-markdown",
    "sitemap.valid",
    "llms.discovery-link",
    "markdown.url-fallback",
    "jsonld.syntax",
    "robots.ai-search-access",
    "robots.content-signal",
    "link.headers-discovery",
)


@pytest.mark.parametrize("path", sorted(public_pages()))
def test_agentmarkup_crawlability(live_url, path):
    port = urlsplit(live_url).port
    result = subprocess.run(
        ["node", "scripts/audit_local.mjs", str(port), path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    findings = [
        f'{finding["code"]}: {finding["detail"]}'
        for finding in report["findings"]
        if finding["level"] == "error"
    ]
    for finding in report["findings"]:
        if finding["level"] == "warn":
            warnings.warn(f'{path} {finding["code"]}: {finding["detail"]}', stacklevel=1)
    # The scored checks use the homepage and a sample. These signals apply to
    # the requested page, so a regression outside the sample also fails CI.
    passed_signals = {finding["code"] for finding in report["findings"] if finding["level"] == "pass"}
    findings.extend(f"Missing page signal: {code}" for code in REQUIRED_PAGE_SIGNALS if code not in passed_signals)
    checks = {check["id"]: check for check in report["score"]["checks"]}
    for check_id in REQUIRED_CHECKS:
        check = checks.get(check_id)
        if check is None or check["status"] != "pass":
            evidence = check["evidence"] if check else "missing audit result"
            findings.append(f"{check_id}: {evidence}")
    assert not findings, f'AgentMarkup for {path} (score {report["score"]["score"]}):\n' + "\n".join(findings)
