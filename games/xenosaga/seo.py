from __future__ import annotations

import html
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any


SITE_ORIGIN = "https://ludex.games"
XENOSAGA_PATH = "/xenosaga"
XENOSAGA_URL = f"{SITE_ORIGIN}{XENOSAGA_PATH}"
XENOSAGA_TITLE = "Xenosaga Enemy Database: Stats, Weaknesses & Drops | Ludex"
XENOSAGA_DESCRIPTION = (
    "Search all 325 enemies from Xenosaga Episodes I, II and III. Compare HP, "
    "weaknesses, resistances, EXP, drops, stealable items and boss stats."
)
XENOSAGA_SOCIAL_IMAGE_URL = (
    f"{SITE_ORIGIN}/assets/favicon/web-app-manifest-512x512.png"
)

DATABASE_PATH = Path(__file__).resolve().parents[2] / "assets" / "xenosaga" / "xenosaga.db"

EPISODES = (
    {
        "id": "episode-1",
        "label": "Xenosaga Episode I: Der Wille zur Macht",
        "table": "episode1",
        "source_label": "Episode I Enemies FAQ on GameFAQs",
        "source_url": (
            "https://gamefaqs.gamespot.com/ps2/519264-xenosaga-episode-i-"
            "der-wille-zur-macht/faqs/22927"
        ),
    },
    {
        "id": "episode-2",
        "label": "Xenosaga Episode II: Jenseits von Gut und Böse",
        "table": "episode2",
        "source_label": "Episode II Enemy FAQ on IGN",
        "source_url": (
            "https://www.ign.com/articles/2005/04/06/xenosaga-episode-ii-"
            "jenseits-von-gut-und-bose-enemy-faq-545281"
        ),
    },
    {
        "id": "episode-3",
        "label": "Xenosaga Episode III: Also sprach Zarathustra",
        "table": "episode3",
        "source_label": "Episode III Enemy FAQ on GameFAQs",
        "source_url": (
            "https://gamefaqs.gamespot.com/ps2/929933-xenosaga-episode-iii-"
            "also-sprach-zarathustra/faqs/45192"
        ),
    },
)


def _escape(value: Any) -> str:
    """Return a safe, readable HTML representation of a database value."""

    if value is None or value == "":
        return "&mdash;"
    return html.escape(str(value))


def _render_episode_table(
    connection: sqlite3.Connection,
    *,
    episode_id: str,
    episode_label: str,
    table_name: str,
) -> tuple[str, int]:
    """Render one complete episode table as semantic, non-JavaScript HTML."""

    columns = [
        row[1]
        for row in connection.execute(f'PRAGMA table_info("{table_name}")')
        if row[1] != "uuid"
    ]
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    rows = connection.execute(
        f'SELECT {quoted_columns} FROM "{table_name}" ORDER BY "Name"'
    ).fetchall()

    header_cells = "".join(
        f'<th scope="col">{html.escape(column)}</th>' for column in columns
    )
    body_rows: list[str] = []
    for row in rows:
        name_cell, *remaining_cells = row
        cells = [f'<th scope="row">{_escape(name_cell)}</th>']
        cells.extend(f"<td>{_escape(value)}</td>" for value in remaining_cells)
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = (
        f'<section id="{episode_id}" class="mb-5">'
        f"<h2>{html.escape(episode_label)} enemies</h2>"
        '<div class="table-responsive">'
        '<table class="table table-sm table-striped table-hover align-middle">'
        f"<caption>{len(rows)} enemies and their game statistics.</caption>"
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
        "</section>"
    )
    return table_html, len(rows)


@lru_cache(maxsize=1)
def build_xenosaga_static_html() -> str:
    """Build the crawlable and no-JavaScript version of the database page."""

    episode_tables: list[str] = []
    episode_counts: list[tuple[str, str, int]] = []
    with sqlite3.connect(DATABASE_PATH) as connection:
        for episode in EPISODES:
            table_html, count = _render_episode_table(
                connection,
                episode_id=episode["id"],
                episode_label=episode["label"],
                table_name=episode["table"],
            )
            episode_tables.append(table_html)
            episode_counts.append((episode["id"], episode["label"], count))

    total_enemies = sum(count for _, _, count in episode_counts)
    episode_links = "".join(
        f'<li><a href="#{episode_id}">{html.escape(label)}</a> '
        f"({count} records)</li>"
        for episode_id, label, count in episode_counts
    )
    source_links = "".join(
        f'<li><a href="{html.escape(episode["source_url"], quote=True)}">'
        f'{html.escape(episode["source_label"])}</a></li>'
        for episode in EPISODES
    )

    return (
        '<main id="xenosaga-static-content" class="container-fluid pb-5">'
        '<article aria-labelledby="xenosaga-page-heading">'
        '<header class="card card-body mb-3">'
        '<h1 id="xenosaga-page-heading" class="card-title">'
        "Xenosaga Enemy Database"
        "</h1>"
        '<p class="lead">A complete, mobile-friendly reference for enemies in '
        "Xenosaga Episodes I, II and III.</p>"
        f"<p>Browse {total_enemies} enemy records with HP, experience, weaknesses, "
        "resistances, item drops, stealable items, and other episode-specific "
        "battle statistics. The interactive version adds searching, sorting, and "
        "column filters when JavaScript is available.</p>"
        "<nav aria-label=\"Xenosaga episode index\"><h2>Choose an episode</h2>"
        f"<ul>{episode_links}</ul></nav>"
        "</header>"
        f"{''.join(episode_tables)}"
        '<section id="sources" class="card card-body">'
        "<h2>Sources and methodology</h2>"
        "<p>The database was compiled from community enemy guides and normalized "
        "into searchable tables. Episode I and III data were extracted and checked "
        "programmatically; Episode II data was transcribed manually. Item effect "
        "descriptions are supplemented from Xenoseries Wiki item lists.</p>"
        f"<ul>{source_links}</ul>"
        '<p><a href="https://github.com/perfectly-preserved-pie/ludex/tree/main/'
        'games/xenosaga">View the database code and documentation on GitHub</a> or '
        '<a href="mailto:hey@ludex.games">report a correction</a>.</p>'
        "</section>"
        "</article>"
        "</main>"
    )


def build_xenosaga_json_ld() -> str:
    """Return JSON-LD describing the visible Xenosaga database content."""

    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{SITE_ORIGIN}/#website",
                "url": f"{SITE_ORIGIN}/",
                "name": "Ludex",
                "description": "Game tools, databases, and reference pages.",
            },
            {
                "@type": "Dataset",
                "@id": f"{XENOSAGA_URL}#dataset",
                "name": "Xenosaga Enemy Database",
                "description": XENOSAGA_DESCRIPTION,
                "url": XENOSAGA_URL,
                "creator": {
                    "@type": "Organization",
                    "name": "Ludex",
                    "url": f"{SITE_ORIGIN}/",
                },
                "isBasedOn": [episode["source_url"] for episode in EPISODES],
                "keywords": [
                    "Xenosaga enemies",
                    "Xenosaga enemy database",
                    "Xenosaga enemy stats",
                    "Xenosaga weaknesses",
                    "Xenosaga item drops",
                ],
            },
            {
                "@type": "WebPage",
                "@id": f"{XENOSAGA_URL}#webpage",
                "url": XENOSAGA_URL,
                "name": XENOSAGA_TITLE,
                "description": XENOSAGA_DESCRIPTION,
                "isPartOf": {"@id": f"{SITE_ORIGIN}/#website"},
                "mainEntity": {"@id": f"{XENOSAGA_URL}#dataset"},
                "breadcrumb": {"@id": f"{XENOSAGA_URL}#breadcrumb"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{XENOSAGA_URL}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Ludex",
                        "item": f"{SITE_ORIGIN}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Xenosaga Enemy Database",
                        "item": XENOSAGA_URL,
                    },
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )


def build_xenosaga_head_metadata(existing_metas: str) -> str:
    """Replace Dash's generic social metadata with Xenosaga-specific tags."""

    meta_pattern = re.compile(
        r'\s*<meta\s+(?:name|property)="(?:description|robots|twitter:[^"]+|og:[^"]+)"[^>]*>',
        flags=re.IGNORECASE,
    )
    cleaned_metas = meta_pattern.sub("", existing_metas).strip()
    description = html.escape(XENOSAGA_DESCRIPTION, quote=True)
    title = html.escape(XENOSAGA_TITLE, quote=True)
    canonical_url = html.escape(XENOSAGA_URL, quote=True)
    image_url = html.escape(XENOSAGA_SOCIAL_IMAGE_URL, quote=True)

    page_tags = (
        f'<meta name="description" content="{description}">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        f'<meta property="og:title" content="{title}">'
        '<meta property="og:type" content="website">'
        '<meta property="og:site_name" content="Ludex">'
        f'<meta property="og:url" content="{canonical_url}">'
        f'<meta property="og:description" content="{description}">'
        f'<meta property="og:image" content="{image_url}">'
        '<meta property="og:image:width" content="512">'
        '<meta property="og:image:height" content="512">'
        '<meta property="og:image:alt" content="Ludex">'
        '<meta name="twitter:card" content="summary">'
        f'<meta name="twitter:title" content="{title}">'
        f'<meta name="twitter:description" content="{description}">'
        f'<meta name="twitter:image" content="{image_url}">'
        '<meta name="twitter:image:alt" content="Ludex">'
        f'<link rel="canonical" href="{canonical_url}">'
        '<script type="application/ld+json">'
        f"{build_xenosaga_json_ld()}"
        "</script>"
    )
    return f"{cleaned_metas}\n      {page_tags}"
