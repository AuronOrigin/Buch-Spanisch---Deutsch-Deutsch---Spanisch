#!/usr/bin/env python3
"""Erzeugt ein druckfertiges A4-PDF aus den Markdown-Kapiteln.

Abhängigkeiten (im .venv): markdown, xhtml2pdf
Aufruf:  python build_pdf.py
Ergebnis: buch.pdf
"""
import os
import re
import glob
import markdown
from xhtml2pdf import pisa

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "buch.pdf")

# Reihenfolge der Kapitel (relativer Pfad, Anzeigetitel für das Inhaltsverzeichnis)
CHAPTERS = [
    ("kapitel/00-einleitung.md",        "Einleitung – Wie man dieses Buch nutzt"),
    ("kapitel/01-begruessungen.md",     "1 · Begrüßungen & Vorstellungen"),
    ("kapitel/02-familie.md",           "2 · Familie & Personen"),
    ("kapitel/03-essen.md",             "3 · Essen & Trinken"),
    ("kapitel/04-einkaufen.md",         "4 · Einkaufen & Supermarkt"),
    ("kapitel/05-wohnen.md",            "5 · Wohnen & Haus"),
    ("kapitel/06-arbeit.md",            "6 · Arbeit & Beruf"),
    ("kapitel/07-reisen.md",            "7 · Reisen & Verkehr"),
    ("kapitel/08-zeit-wetter.md",       "8 · Zeit & Wetter"),
    ("kapitel/09-gesundheit.md",        "9 · Gesundheit & Körper"),
    ("kapitel/10-freizeit.md",          "10 · Freizeit & Hobbys"),
    ("anhang/11-grammatik-referenz.md", "Anhang · Grammatik-Referenz"),
    ("anhang/12-loesungen.md",          "Anhang · Lösungen"),
    ("anhang/13-woerterverzeichnis.md", "Anhang · Wörterverzeichnis"),
]

MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

FONT_DIR = os.path.join(ROOT, "fonts")

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
@page {
    size: A4;
    margin: 2cm 1.8cm 2.2cm 1.8cm;
    @frame header {
        -pdf-frame-content: header;
        left: 1.8cm; width: 16.4cm; top: 0.8cm; height: 1cm;
    }
    @frame footer {
        -pdf-frame-content: footer;
        left: 1.8cm; width: 16.4cm; bottom: 0.8cm; height: 1cm;
    }
}
body {
    font-family: DejaVu;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #1a1a1a;
}
h1 {
    font-size: 20pt;
    color: #10355e;
    border-bottom: 2px solid #10355e;
    padding-bottom: 4px;
    margin-top: 0;
    page-break-before: always;
}
h1.first { page-break-before: auto; }
h2 {
    font-size: 14pt;
    color: #1f5fa8;
    margin-top: 18px;
    border-left: 4px solid #1f5fa8;
    padding-left: 8px;
}
h3 {
    font-size: 11.5pt;
    color: #333;
    margin-top: 12px;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0 14px 0;
    font-size: 9.5pt;
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
    font-style: italic;
    color: #333;
}
code {
    font-family: DejaVuMono;
    background: #eef1f4;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 9pt;
}
hr { border: none; border-top: 1px solid #ccc; margin: 14px 0; }

/* Titelseite */
.cover {
    text-align: center;
    padding-top: 5cm;
    page-break-after: always;
}
.cover .title { font-size: 38pt; color: #10355e; font-weight: bold; }
.cover .subtitle { font-size: 16pt; color: #1f5fa8; margin-top: 14px; }
.cover .meta { font-size: 11pt; color: #555; margin-top: 3cm; }
.cover .rule { width: 40%; border-top: 2px solid #1f5fa8; margin: 1cm auto; }

/* Inhaltsverzeichnis */
.toc { margin: 0; padding: 0; list-style: none; }
.toc li { margin: 8px 0; font-size: 12pt; border-bottom: 1px dotted #ccc; padding-bottom: 4px; }

#header { font-size: 8pt; color: #777; text-align: right; }
#footer { font-size: 8pt; color: #777; text-align: center; }
"""

COVER = """
<div class="cover">
    <div class="title">Puente – Die Brücke</div>
    <div class="rule"></div>
    <div class="subtitle">Spanisch&nbsp;↔&nbsp;Deutsch<br/>Lehr- und Übersetzungsbuch (A1–A2)</div>
    <div class="meta">
        Zweisprachiges Lehrbuch mit Vokabeln, Beispielsätzen,<br/>
        Grammatik und Übungen in beiden Richtungen.<br/><br/>
        Erstellt mit Arena.ai
    </div>
</div>
"""

def build_toc():
    items = "".join(f"<li>{title}</li>" for _, title in CHAPTERS)
    return (
        "<h1 class='first'>Inhalt</h1>"
        "<ul class='toc'>" + items + "</ul>"
        "<p style='margin-top:1.5cm; font-size:9pt; color:#666;'>"
        "Jede Lerneinheit enthält Vokabeln (Spanisch → Deutsch und Deutsch → Spanisch), "
        "Beispielsätze, einen Grammatik-Schwerpunkt, kleine Übungen und die Lösungen.</p>"
    )

def md_to_html(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    MD.reset()
    return MD.convert(text)

def main():
    parts = [COVER, build_toc()]
    first = True
    for path, _title in CHAPTERS:
        html = md_to_html(path)
        # erste Überschrift soll NICHT vorher umbrechen (folgt auf Inhalt)
        if first:
            html = html.replace("<h1", "<h1 class='first'", 1)
            first = False
        parts.append(html)

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{CSS}</style>
</head>
<body>
<div id="header">Puente – Die Brücke: Spanisch ↔ Deutsch</div>
<div id="footer">Seite <pdf:pagenumber/> von <pdf:pagecount/></div>
{''.join(parts)}
</body>
</html>"""

    with open(OUT, "wb") as f:
        pisa_status = pisa.CreatePDF(src=full_html, dest=f)
    if pisa_status.err:
        print("FEHLER beim PDF-Erzeugen:", pisa_status.err)
        raise SystemExit(1)
    size = os.path.getsize(OUT)
    print(f"OK: {OUT} ({size/1024:.0f} KB)")

if __name__ == "__main__":
    main()
