"""Digest assembly, rendering (Markdown/HTML/text) and delivery via Resend."""

from jobbot.digest.build import Digest, build_digest
from jobbot.digest.render import render_html, render_markdown, render_text
from jobbot.digest.send import ResendError, send_digest

__all__ = [
    "Digest",
    "ResendError",
    "build_digest",
    "render_html",
    "render_markdown",
    "render_text",
    "send_digest",
]
