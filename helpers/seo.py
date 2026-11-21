"""Social previews served in the initial HTML, including for non-JS clients."""

import json
import os
import re
from datetime import date
from html import escape


SITE_ORIGIN = "https://ludex.games"
SITE_DESCRIPTION = "Game databases, calculators and reference pages for Xenosaga and Clair Obscur: Expedition 33."
PROJECT_URL = "https://github.com/perfectly-preserved-pie/ludex"
CONTACT_EMAIL = "hey@ludex.games"
PROJECT_INFO_PATH = "/about"
SOCIAL_IMAGE_URL = f"{SITE_ORIGIN}/assets/social-preview.png"
SOCIAL_IMAGE_ALT = "Ludex — Game databases, calculators and reference pages. Xenosaga and Clair Obscur: Expedition 33."

PAGE_GUIDANCE = {
    "/": (
        "Use the Xenosaga Enemy Database to compare enemies across Episodes I, II and III. "
        "Each episode has its own table and fields. The HTML tables and Markdown edition include "
        "the complete dataset and link back to the original enemy guides.",
        "For Clair Obscur: Expedition 33, use the skill reference to look up damage multipliers "
        "and hit counts, the calculator to compare builds, or the zone reference to plan where "
        "to explore next.",
    ),
    "/exp33/calculator": (
        "Choose a character, skill, and weapon, then enter build stats and relevant bonuses. "
        "The calculator estimates damage for the selected setup and can compare two builds. "
        "Change one setting at a time to see how it affects the estimate.",
        "A supported Expedition 33 save file can fill in build details. You can also enter a build "
        "manually. Use the skill damage reference to check hit counts and multipliers, and enable "
        "JavaScript to run a calculation or import a save.",
    ),
    "/exp33/skilldamage": (
        "Pick a character to browse their skills. Compare damage multipliers and hit counts, "
        "or open a skill's detail view to inspect its per-hit information.",
        "Use the damage calculator when you want a build-specific estimate that accounts for "
        "weapons, character stats and bonuses. Use this reference to check the underlying "
        "skill data before changing a build.",
    ),
    "/exp33/zonelevels": (
        "Use the zone level reference to compare recommended levels when deciding where to explore. "
        "Filter the interactive table by level to find areas around your party's current level.",
        "The levels are community guidance, and encounters can vary with equipment and builds. "
        "Consult the skill damage reference or calculator if you want to compare combat setups "
        "before attempting a tougher area.",
    ),
}

PROJECT_SECTIONS = (
    ("about", "About", "Ludex is an independent, open-source project for game reference data and build tools."),
    ("contact", "Contact", "Send corrections or questions to", CONTACT_EMAIL),
    (
        "privacy",
        "Privacy",
        "Ludex uses Plausible and Rybbit for site analytics. If you choose to import a calculator "
        "save, the file is sent to the server to extract build details. The calculator's analytics "
        "event records whether the import succeeded or failed.",
    ),
)


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
        ("/llms.txt", "text/plain"),
        (f"{SITE_ORIGIN}{markdown_path}", "text/markdown"),
    )


def publisher_entity() -> dict:
    """Identify the project and its public support contact."""

    return {
        "@type": "Organization",
        "@id": f"{SITE_ORIGIN}/#publisher",
        "name": "Ludex",
        "url": f"{SITE_ORIGIN}/",
        "description": SITE_DESCRIPTION,
        "sameAs": PROJECT_URL,
        "contactPoint": {"@type": "ContactPoint", "email": CONTACT_EMAIL, "contactType": "support"},
    }


def website_entity() -> dict:
    """Identify the same Ludex site in every page's structured data."""

    return {
        "@type": "WebSite",
        "@id": f"{SITE_ORIGIN}/#website",
        "url": f"{SITE_ORIGIN}/",
        "name": "Ludex",
        "description": SITE_DESCRIPTION,
        "inLanguage": "en",
        "publisher": {"@id": f"{SITE_ORIGIN}/#publisher"},
    }


def build_page_structured_data(page: dict, *entities: dict) -> str:
    """Describe a public page and its relationship to Ludex."""

    site = website_entity()
    url = f'{SITE_ORIGIN}{page["path"]}'
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            site,
            publisher_entity(),
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["description"],
                "isPartOf": {"@id": site["@id"]},
            },
            *entities,
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
    guidance = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in PAGE_GUIDANCE.get(page["path"], ()))
    noscript = (
        '<noscript><p>Enable JavaScript to use the interactive tools.</p></noscript>'
        if page["path"] != PROJECT_INFO_PATH else ""
    )
    project = ""
    if page["path"] == "/":
        project_links = " · ".join(
            f'<a href="{PROJECT_INFO_PATH}#{slug}">{title}</a>' for slug, title, *_ in PROJECT_SECTIONS
        )
        project = f'<nav aria-label="Project information">{project_links}</nav>'
    elif page["path"] == PROJECT_INFO_PATH:
        project = "".join(
            f'<section id="{slug}"><h2>{title}</h2><p>{escape(body)}'
            + (f' <a href="mailto:{email[0]}">{email[0]}</a>.' if email else "")
            + "</p></section>"
            for slug, title, body, *email in PROJECT_SECTIONS
        )
    return (
        '<main class="container py-4">'
        f'<h1>{escape(page["title"].removesuffix(" | Ludex"))}</h1>'
        f'<p>{escape(page["description"])}</p>{guidance}{noscript}'
        f'{project}'
        f'<nav aria-label="Ludex pages"><ul>{links}</ul></nav>'
        '</main>'
    )


def build_markdown(page: dict, details: str, *, frontmatter: bool) -> str:
    """Render a Markdown companion with its canonical page and optional dataset."""

    title = page["title"].removesuffix(" | Ludex")
    canonical = f'{SITE_ORIGIN}{page["path"]}'
    guidance = "".join(f"{paragraph}\n\n" for paragraph in PAGE_GUIDANCE.get(page["path"], ()))
    if page["path"] == PROJECT_INFO_PATH:
        guidance = "".join(
            f"## {heading}\n\n{body}"
            + (f" [{email[0]}](mailto:{email[0]})." if email else "")
            + "\n\n"
            for _, heading, body, *email in PROJECT_SECTIONS
        )
    metadata = f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ncanonical: {canonical}\n---\n\n" if frontmatter else ""
    return (
        f'{metadata}# {title}\n\n{page["description"]}\n\n'
        f'[Open the interactive page]({canonical})\n\n{guidance}{details}'
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
