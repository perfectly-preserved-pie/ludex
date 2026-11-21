"""Social previews served in the initial HTML, including for non-JS clients."""

import json
import os
import re
from datetime import date
from html import escape


SITE_ORIGIN = "https://ludex.games"
SITE_DESCRIPTION = "Game databases, calculators and reference pages for Xenosaga and Clair Obscur: Expedition 33."
SOCIAL_IMAGE_URL = f"{SITE_ORIGIN}/assets/social-preview.png"
SOCIAL_IMAGE_ALT = "Ludex — Game databases, calculators and reference pages. Xenosaga and Clair Obscur: Expedition 33."


def build_social_head_metadata(
    existing_metas: str, *, title: str, description: str, path: str
) -> str:
    """Replace Dash's default tags with one complete, canonical social card."""
    cleaned_metas = re.sub(
        r'\s*<meta\s+(?:name|property)="(?:description|twitter:[^"]+|og:[^"]+)"[^>]*>',
        "",
        existing_metas,
        flags=re.IGNORECASE,
    ).strip()
    title, description, url, image_url, image_alt = (
        escape(value, quote=True)
        for value in (title, description, f"{SITE_ORIGIN}{path}", SOCIAL_IMAGE_URL, SOCIAL_IMAGE_ALT)
    )
    tags = (
        f'<meta name="description" content="{description}">'
        f'<meta property="og:title" content="{title}">'
        '<meta property="og:type" content="website">'
        '<meta property="og:site_name" content="Ludex">'
        f'<meta property="og:url" content="{url}">'
        f'<meta property="og:description" content="{description}">'
        f'<meta property="og:image" content="{image_url}">'
        '<meta property="og:image:type" content="image/png">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        f'<meta property="og:image:alt" content="{image_alt}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:url" content="{url}">'
        f'<meta name="twitter:title" content="{title}">'
        f'<meta name="twitter:description" content="{description}">'
        f'<meta name="twitter:image" content="{image_url}">'
        f'<meta name="twitter:image:alt" content="{image_alt}">'
        f'<link rel="canonical" href="{url}">'
    )
    return f"{cleaned_metas}\n      {tags}"


def alternate_links(path: str) -> tuple[tuple[str, str], ...]:
    """Return the site manifest and page-specific Markdown discovery links."""

    markdown_path = "/index.md" if path == "/" else f"{path}.md"
    return (
        (f"{SITE_ORIGIN}/llms.txt", "text/plain"),
        (f"{SITE_ORIGIN}{markdown_path}", "text/markdown"),
    )


def website_entity() -> dict[str, str]:
    """Identify the same Ludex site in every page's structured data."""

    return {
        "@type": "WebSite",
        "@id": f"{SITE_ORIGIN}/#website",
        "url": f"{SITE_ORIGIN}/",
        "name": "Ludex",
        "description": SITE_DESCRIPTION,
        "inLanguage": "en",
    }


def build_page_structured_data(page: dict) -> str:
    """Describe a public page and its relationship to Ludex."""

    site = website_entity()
    url = f'{SITE_ORIGIN}{page["path"]}'
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            site,
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["description"],
                "isPartOf": {"@id": site["@id"]},
            },
        ],
    }
    return f'<script type="application/ld+json">{serialize_json_ld(graph)}</script>'


def serialize_json_ld(data: dict) -> str:
    """Encode structured data that can be safely embedded in HTML."""

    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", r"\u003c")


def build_initial_page(page: dict, pages: dict) -> str:
    """Publish a readable introduction and navigation before React mounts."""

    links = "".join(
        f'<li><a href="{escape(path)}">{escape(item["title"].removesuffix(" | Ludex"))}</a></li>'
        for path, item in sorted(pages.items())
        if path != page["path"]
    )
    return (
        '<main class="container py-4">'
        f'<h1>{escape(page["title"].removesuffix(" | Ludex"))}</h1>'
        f'<p>{escape(page["description"])}</p>'
        '<noscript><p>Enable JavaScript to use the interactive tools.</p></noscript>'
        f'<nav aria-label="Ludex pages"><ul>{links}</ul></nav>'
        '</main>'
    )


def build_markdown(page: dict, details: str, *, frontmatter: bool) -> str:
    """Render a Markdown companion with its canonical page and optional dataset."""

    title = page["title"].removesuffix(" | Ludex")
    canonical = f'{SITE_ORIGIN}{page["path"]}'
    metadata = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ncanonical: {canonical}\n---\n\n" if frontmatter else ""
    return (
        f'{metadata}# {title}\n\n{page["description"]}\n\n'
        f'[Open the interactive page]({canonical})\n\n{details}'
    )


def build_sitemap_urls(paths: list[str]) -> str:
    """Add build-provided source dates when valid metadata is available."""

    try:
        dates = json.loads(os.environ.get("SITE_PAGE_LASTMOD", "{}"))
    except ValueError:
        dates = {}
    if not isinstance(dates, dict):
        dates = {}

    entries = []
    for path in paths:
        lastmod = dates.get(path)
        date_tag = ""
        if isinstance(lastmod, str):
            try:
                date_tag = f"<lastmod>{date.fromisoformat(lastmod).isoformat()}</lastmod>"
            except ValueError:
                pass
        entries.append(f"<url><loc>{escape(SITE_ORIGIN + path)}</loc>{date_tag}</url>")
    return "".join(entries)
