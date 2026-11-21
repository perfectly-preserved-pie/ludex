# Crawler regression checks

After changes to public HTML, metadata, routing, crawler files, or deployment
settings that affect those responses, run `npm ci --ignore-scripts` if needed
and `uv run --frozen pytest -q --run-geo -m geo` against the local build.
Fix crawler regressions and rerun the check. The overall score and advisory
warnings are diagnostic. Report a blocker if the audit cannot run.
