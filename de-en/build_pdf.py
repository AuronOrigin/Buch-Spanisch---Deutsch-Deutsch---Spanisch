#!/usr/bin/env python3
"""Erzeugt ein druckfertiges A4-PDF im Buchdruck-Layout aus den Markdown-Kapiteln.

Buch: Bridge – Die Brücke: Deutsch ↔ Englisch
(Lehr- und Übersetzungsbuch, A1–A2)

Features:
  - Gespiegelte Ränder mit Bundsteg (innen breiter) -> Hardcover/Buchdruck-Look
  - Etwas groessere Schrift, komfortable Zeilenhoehe
  - Inhaltsverzeichnis mit echten, anklickbaren Seitenzahlen (2-Pass-Build)

Abhaengigkeiten (im .venv): markdown, xhtml2pdf, pymupdf
Aufruf:  python de-en/build_pdf.py
Ergebnis: de-en/buch_de_en.pdf
"""
import os
import re
import io
import sys
import markdown
import fitz  # pymupdf
from xhtml2pdf import pisa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BOOK_DIR, "buch_de_en.pdf")
FONT_DIR = os.path.join(BOOK_DIR, "fonts")

# (relativer Pfad, TOC-Anzeige, Anker-ID, Such-Schluessel im PDF-Text)
CHAPTERS = [
    ("de-en/kapitel/00-einleitung.md",        "Einleitung – Wie man dieses Buch nutzt",        "chap0",  "Kapitel 0 – Einleitung"),
    ("de-en/kapitel/01-begruessungen.md",     "1 · Begrüßungen & Vorstellungen",              "chap1",  "Kapitel 1 – Begrüßungen"),
    ("de-en/kapitel/02-familie.md",           "2 · Familie & Personen",                        "chap2",  "Kapitel 2 – Familie"),
    ("de-en/kapitel/03-essen.md",             "3 · Essen & Trinken",                           "chap3",  "Kapitel 3 – Essen"),
    ("de-en/kapitel/04-einkaufen.md",         "4 · Einkaufen & Supermarkt",                    "chap4",  "Kapitel 4 – Einkaufen"),
    ("de-en/kapitel/05-wohnen.md",           "5 · Wohnen & Haus",                             "chap5",  "Kapitel 5 – Wohnen"),
    ("de-en/kapitel/06-arbeit.md",            "6 · Arbeit & Beruf",                            "chap6",  "Kapitel 6 – Arbeit"),
    ("de-en/kapitel/07-reisen.md",           "7 · Reisen & Verkehr",                          "chap7",  "Kapitel 7 – Reisen"),
    ("de-en/kapitel/08-zeit-wetter.md",      "8 · Zeit & Wetter",                             "chap8",  "Kapitel 8 – Zeit"),
    ("de-en/kapitel/09-gesundheit.md",        "9 · Gesundheit & Körper",                      "chap9",  "Kapitel 9 – Gesundheit"),
    ("de-en/kapitel/10-freizeit.md",         "10 · Freizeit & Hobbys",                        "chap10", "Kapitel 10 – Freizeit"),
    ("de-en/anhang/11-grammatik-referenz.md", "Anhang: Grammatik-Referenz",                   "chap11", "Anhang – Grammatik"),
    ("de-en/anhang/12-loesungen.md",          "Anhang: Lösungen",                              "chap12", "Anhang – Lösungen"),
    ("de-en/anhang/13-woerterverzeichnis.md", "Anhang: Wörterverzeichnis",                    "chap13", "Anhang – Wörterverzeichnis"),
]

MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

CSS = """
@font-face {
    font-family: DejaVu;
    src: url(file://""" + FONT_DIR + """/DejaVuSans.ttf);
}
@font-face {
    font-family: DejaVu;
    font-weight: bold;
    src: url(file://""" + FONT_DIR + """/DejaVuSans-Bold.ttf);
}
@font-face {
    font-family: DejaVuMono;
    src: url(file://""" + FONT_DIR + """/DejaVuSansMono.ttf);
}

/* Buchdruck: gespiegelte Raender mit Bundsteg (innen breiter) */
@page {
    size: A4;
    margin-top: 2cm;
    margin-bottom: 2.2cm;
    margin-left: 2cm;
    margin-right: 2cm;
    @frame header_frame {
        -pdf-frame-content: header;
        left: 1.5cm; width: 18.0cm; top: 0.7cm; height: 1cm;
    }
    @frame footer_frame {
        -pdf-frame-content: footer;
        left: 1.5cm; width: 18.0cm; bottom: 0.7cm; height: 1cm;
    }
}
@page :left {
    margin-left: 3.2cm;   /* Bundsteg auf der Innenseite */
    margin-right: 2cm;
}
@page :right {
    margin-left: 2cm;
    margin-right: 3.2cm;
}

body {
    font-family: DejaVu;
    font-size: 11.5pt;
    line-height: 1.5;
    color: #1a1a1a;
}
h1 {
    font-size: 22pt;
    color: #10355e;
    border-bottom: 2px solid #10355e;
    padding-bottom: 4px;
    margin-top: 0;
    page-break-before: always;
}
h1.first { page-break-before: auto; }
h2 {
    font-size: 15pt;
    color: #1f5fa8;
    margin-top: 20px;
    border-left: 4px solid #1f5fa8;
    padding-left: 8px;
}
h3 {
    font-size: 12.5pt;
    color: #333;
    margin-top: 14px;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0 16px 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid #b9c4d0;
    padding: 4px 7px;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #e8eef5;
    font-weight: bold;
}
tr:nth-child(even) td { background-color: #f5f8fb; }
ul, ol { margin: 6px 0 12px 0; padding-left: 22px; }
li { margin: 3px 0; }
strong { color: #10355e; }
em { color: #555; }
blockquote {
    background: #f0f5fa;
    border-left: 4px solid #1f5fa8;
    margin: 10px 0;
    padding: 8px 12px;
    color: #333;
}
code {
    font-family: DejaVuMono;
    background: #eef1f4;
    padding: 1px 4px;
    font-size: 9.5pt;
}
hr { border: none; border-top: 1px solid #ccc; margin: 14px 0; }

/* Inhaltsverzeichnis */
.toc { border-collapse: collapse; width: 100%; font-size: 11.5pt; margin-top: 10px; }
.toc td { padding: 5px 0; border-bottom: 1px dotted #b9c4d0; vertical-align: bottom; }
.toc td.t a { color: #10355e; text-decoration: none; }
.toc td.t a:hover { text-decoration: underline; }
.toc td.p { text-align: right; white-space: nowrap; color: #10355e; font-weight: bold; }

/* Titelseite */
.cover {
    text-align: center;
    padding-top: 5cm;
    page-break-after: always;
}
.cover .title { font-size: 40pt; color: #10355e; font-weight: bold; }
.cover .rule { width: 40%; border-top: 2px solid #1f5fa8; margin: 1cm auto; }
.cover .subtitle { font-size: 17pt; color: #1f5fa8; margin-top: 14px; }
.cover .meta { font-size: 11.5pt; color: #555; margin-top: 3cm; line-height: 1.6; }

#header { font-size: 8pt; color: #777; text-align: right; }
#footer { font-size: 8pt; color: #777; text-align: center; }
"""

COVER = """
<div class="cover">
    <div class="title">Bridge – Die Brücke</div>
    <div class="rule"></div>
    <div class="subtitle">Deutsch&nbsp;↔&nbsp;Englisch<br/>Lehr- und Übersetzungsbuch (A1–A2)</div>
    <div class="meta">
        Zweisprachiges Lehrbuch mit Vokabeln, Beispielsätzen,<br/>
        Grammatik und Übungen in beiden Richtungen.<br/><br/>
        Erstellt mit Arena.ai
    </div>
</div>
"""


def build_toc(pages):
    rows = []
    for _path, label, anchor, _key in CHAPTERS:
        p = pages.get(anchor) if pages else ""
        rows.append(
            f'<tr><td class="t"><a href="#{anchor}">{label}</a></td>'
            f'<td class="p">{p}</td></tr>'
        )
    return (
        "<h1 class='first'>Inhalt</h1>"
        '<table class="toc">' + "".join(rows) + "</table>"
        "<p style='margin-top:1.5cm; font-size:9.5pt; color:#666;'>"
        "Jede Lerneinheit enthält Vokabeln (Deutsch → Englisch und Englisch → Deutsch), "
        "Beispielsätze, einen Grammatik-Schwerpunkt, kleine Übungen und die Lösungen.</p>"
    )


def md_to_html(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    MD.reset()
    return MD.convert(text)


def add_anchor(html, anchor):
    return re.sub(r"<h1\b", f"<h1 id='{anchor}'", html, count=1)


def build_html(pages):
    parts = [COVER, build_toc(pages)]
    for path, _label, anchor, _key in CHAPTERS:
        html = add_anchor(md_to_html(path), anchor)
        parts.append(html)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{CSS}</style>
</head>
<body>
<div id="header">Bridge – Die Brücke: Deutsch ↔ Englisch</div>
<div id="footer">Seite <pdf:pagenumber/> von <pdf:pagecount/></div>
{''.join(parts)}
</body>
</html>"""


def render(html_str):
    buf = io.BytesIO()
    status = pisa.CreatePDF(src=html_str, dest=buf)
    if status.err:
        raise RuntimeError(f"PDF-Fehler: {status.err}")
    return buf.getvalue()


def find_page(pdf_bytes, key):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i, page in enumerate(doc):
        if key in page.get_text():
            return i + 1
    return None


def main():
    # Pass 1: Seitenzahlen der Kapitel ermitteln
    pdf1 = render(build_html(pages=None))
    pages = {anchor: find_page(pdf1, key) for _p, _l, anchor, key in CHAPTERS}
    missing = [k for k, v in pages.items() if v is None]
    if missing:
        print("WARN: Seitenzahl nicht gefunden für:", missing)

    # Pass 2: endgültiges PDF mit Inhaltsverzeichnis + Seitenzahlen
    with open(OUT, "wb") as f:
        f.write(render(build_html(pages=pages)))
    size = os.path.getsize(OUT)
    doc = fitz.open(OUT)
    print(f"OK: {OUT} ({size/1024:.0f} KB, {doc.page_count} Seiten)")
    print("Inhaltsverzeichnis-Seitenzahlen:", pages)


if __name__ == "__main__":
    main()
