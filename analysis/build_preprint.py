#!/usr/bin/env python
"""Render docs/AlignSSL_SV_manuscript.md to a self-contained preprint PDF.

The manuscript is authored in Markdown with platform artifact markers of the
form ``{{artifact:art_<uuid>}}`` for figure images, because that is what
renders in the project UI. For the PDF we must point at the on-disk figures
instead, so each marker is rewritten to the corresponding ``results/*.png``
before rendering.

The mapping is *derived*, not hard-coded: every image line in the manuscript
begins its alt text with ``Figure N.``, and ``results/figureN_*.png`` is the
file produced by ``analysis/make_figures.py`` for that same N. We assert a
bijection so a renamed figure or a re-pointed marker fails loudly here rather
than silently shipping a PDF with a missing or wrong image.

Pipeline: Markdown -> HTML (python-markdown, tables + fenced code) -> PDF
(WeasyPrint). No LaTeX dependency, which keeps the build runnable in the same
environment as the analysis code.

Usage
-----
    python analysis/build_preprint.py \
        --manuscript docs/AlignSSL_SV_manuscript.md \
        --results-dir results \
        --out docs/AlignSSL_SV_preprint.pdf
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import mimetypes
import re
from pathlib import Path

import markdown as md
from weasyprint import HTML

# Image lines look like:  ![Figure 3. caption ...]({{artifact:art_<uuid>}})
IMG_RE = re.compile(
    r"!\[(?P<alt>Figure\s+(?P<num>\d+)\.[^\]]*)\]\(\{\{artifact:(?P<aid>[^}]+)\}\}\)"
)

CSS = """
@page {
  size: A4;
  margin: 20mm 18mm 20mm 18mm;
  @bottom-center {
    content: counter(page) " / " counter(pages);
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 8pt; color: #666;
  }
}
body {
  font-family: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  font-size: 9.6pt; line-height: 1.45; color: #111; text-align: justify;
  hyphens: auto;
}
h1 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 17pt; line-height: 1.25; margin: 0 0 6pt 0; text-align: left;
  color: #0b2d4d;
}
h2 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 12pt; margin: 16pt 0 5pt 0; text-align: left; color: #0b2d4d;
  border-bottom: 0.6pt solid #c9d4de; padding-bottom: 2pt;
  page-break-after: avoid;
}
h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10.2pt; margin: 12pt 0 4pt 0; text-align: left; color: #14405f;
  page-break-after: avoid;
}
h4 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 9.6pt; margin: 10pt 0 3pt 0; text-align: left; color: #333;
  page-break-after: avoid;
}
p { margin: 0 0 6pt 0; }
hr { border: none; border-top: 0.5pt solid #d8dee4; margin: 12pt 0; }
a { color: #14405f; text-decoration: none; }
code {
  font-family: "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 8.4pt; background: #f4f6f8; padding: 0 2px; border-radius: 2px;
}
pre {
  background: #f4f6f8; padding: 6pt 8pt; border-radius: 3px;
  font-size: 8pt; line-height: 1.35; overflow-wrap: break-word;
  white-space: pre-wrap; page-break-inside: avoid;
}
blockquote {
  margin: 6pt 0; padding: 4pt 10pt; border-left: 2.5pt solid #c9d4de;
  background: #f8fafb; color: #333; font-size: 9pt; text-align: left;
}
table {
  border-collapse: collapse; width: 100%; margin: 8pt 0 10pt 0;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 8.1pt; page-break-inside: avoid;
}
th, td {
  border-top: 0.5pt solid #c9d4de; border-bottom: 0.5pt solid #c9d4de;
  padding: 2.6pt 4pt; text-align: left; vertical-align: top;
}
th { background: #eef2f5; font-weight: 600; }
figure { margin: 10pt 0 12pt 0; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
figcaption {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 8.1pt; color: #333; text-align: left; margin-top: 4pt;
  line-height: 1.35;
}
ul, ol { margin: 0 0 6pt 0; padding-left: 16pt; }
li { margin-bottom: 2.5pt; }
.footer-note {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 7.6pt; color: #777; margin-top: 14pt;
  border-top: 0.5pt solid #d8dee4; padding-top: 5pt;
}
"""


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def resolve_figures(text: str, results_dir: Path) -> tuple[str, dict[int, Path]]:
    """Rewrite artifact markers to embedded on-disk figures.

    Returns the rewritten Markdown and the {figure number -> file} mapping.
    Raises if any figure number has no unique ``results/figureN_*.png``.
    """
    matches = list(IMG_RE.finditer(text))
    if not matches:
        raise SystemExit("no figure markers found in the manuscript")

    used: dict[int, Path] = {}
    for m in matches:
        num = int(m.group("num"))
        hits = sorted(results_dir.glob(f"figure{num}_*.png"))
        if len(hits) != 1:
            raise SystemExit(
                f"Figure {num}: expected exactly one results/figure{num}_*.png, "
                f"found {[h.name for h in hits]}"
            )
        if num in used:
            raise SystemExit(f"Figure {num} is embedded more than once")
        used[num] = hits[0]

    expected = set(range(1, len(matches) + 1))
    if set(used) != expected:
        raise SystemExit(
            f"figure numbering is not contiguous 1..{len(matches)}: got {sorted(used)}"
        )

    def repl(m: re.Match) -> str:
        num = int(m.group("num"))
        alt = m.group("alt").replace('"', "&quot;")
        return (
            f'<figure><img src="{_data_uri(used[num])}" alt="Figure {num}"/>'
            f"<figcaption>{alt}</figcaption></figure>"
        )

    return IMG_RE.sub(repl, text), used


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", default="docs/AlignSSL_SV_manuscript.md")
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--out", default="docs/AlignSSL_SV_preprint.pdf")
    args = ap.parse_args()

    src = Path(args.manuscript)
    text = src.read_text()
    text, figs = resolve_figures(text, Path(args.results_dir))

    body = md.markdown(
        text,
        extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists"],
    )
    stamp = _dt.date.today().isoformat()
    html = (
        "<html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}"
        f"<p class='footer-note'>Preprint build {stamp} — rendered from "
        f"{src.as_posix()} with figures regenerated by analysis/make_figures.py. "
        "Numbers in all tables are reconciled against results/*.csv by "
        "analysis/check_manuscript.py.</p>"
        "</body></html>"
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(src.parent.resolve())).write_pdf(out)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    for n in sorted(figs):
        print(f"  figure {n}: {figs[n].as_posix()}")


if __name__ == "__main__":
    main()
