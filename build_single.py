"""Baut aus index.html + dsa-daten.js + dsa-pregens.js EINE in sich geschlossene
Datei DSA5-Heldenbogen.html zum Verschicken/per-Doppelklick-Öffnen (keine externen Dateien).
Aufruf:  python build_single.py   (vorher generate_daten.py / parse_pregens.py laufen lassen)
"""
from pathlib import Path

html = Path("index.html").read_text(encoding="utf-8")
daten = Path("dsa-daten.js").read_text(encoding="utf-8")
pregens = Path("dsa-pregens.js").read_text(encoding="utf-8")
lore = Path("dsa-lore.js").read_text(encoding="utf-8")
exoten = Path("dsa-exoten.js").read_text(encoding="utf-8")

for tag, js in [('<script src="dsa-daten.js"></script>', daten),
                ('<script src="dsa-pregens.js"></script>', pregens),
                ('<script src="dsa-lore.js"></script>', lore),
                ('<script src="dsa-exoten.js"></script>', exoten)]:
    assert tag in html, f"Tag nicht gefunden: {tag}"
    html = html.replace(tag, "<script>\n" + js.rstrip() + "\n</script>")

out = Path("DSA5-Heldenbogen.html")
out.write_text(html, encoding="utf-8")
assert 'src="dsa-' not in html, "Lokale <script src=dsa-...> nicht eingebettet!"  # CDN-Scripts (Firebase) bleiben extern
assert "window.DSADATEN" in html and "window.DSAPREGENS" in html and "window.DSALORE" in html and "window.DSAEXOTEN" in html, "Daten nicht eingebettet!"
print(f"{out.name} geschrieben: {len(html)//1024} KB. DSA-Daten eingebettet; Firebase wird online vom CDN geladen (nur für die Live-Sync; offline läuft der Bogen lokal weiter).")
