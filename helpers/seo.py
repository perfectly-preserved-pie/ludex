"""Social previews served in the initial HTML, including for non-JS clients."""

import re
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
