import { audit } from "@agentmarkup/audit";

const canonicalOrigin = "https://ludex.games";
const [, , port, path] = process.argv;
if (!/^\d+$/.test(port ?? "") || Number(port) < 1 || Number(port) > 65535 || !path?.startsWith("/")) {
  throw new Error("Usage: node scripts/audit_local.mjs <loopback port> <public page path>");
}
const localOrigin = `http://127.0.0.1:${port}`;

// Keep canonical and sitemap comparisons in the production namespace while
// fetching exclusively from the local app. Preserve redirects for inspection.
function fetchLocal(requestedUrl, init) {
  const url = new URL(requestedUrl);
  if (url.origin !== canonicalOrigin) {
    throw new Error(`Unexpected audit origin: ${url.origin}`);
  }
  return fetch(localOrigin + url.pathname + url.search, { ...init, redirect: "manual" });
}

async function probeLocal(requestedUrl, { userAgent, timeoutMs = 10_000 }) {
  const response = await fetchLocal(requestedUrl, {
    headers: { "user-agent": userAgent },
    signal: AbortSignal.timeout(timeoutMs),
  });
  const body = await response.text();
  return {
    requestedUrl,
    finalUrl: requestedUrl,
    status: response.status,
    ok: response.ok,
    headers: Object.fromEntries(response.headers),
    body,
    bodyBytes: Buffer.byteLength(body),
    redirects: 0,
    blocked: false,
  };
}

const report = await audit(canonicalOrigin + path, {
  score: true,
  fetchImpl: probeLocal,
  collect: { fetchImpl: fetchLocal, minGapMs: 0 },
});
console.log(JSON.stringify(report));
