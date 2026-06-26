# -*- coding: utf-8 -*-
"""Holt Kurzbeschreibungen (Spezies/Kulturen/Professionen) aus Wiki Aventurica.
Quelle: gerenderte /wiki/<Titel>-HTML, Intro-Absaetze vor der ersten Ueberschrift.
Erzeugt dsa-lore.json. Namensaufloesung ueber Kandidaten-Lemmata + Redirect/BKS-Handling.
"""
import json, re, time, sys, urllib.request, urllib.parse
from bs4 import BeautifulSoup

BASE = "https://de.wiki-aventurica.de/wiki/"
UA = {"User-Agent": "DSA-Heldenbogen-Lore/1.0 (privates Hobbyprojekt, Kontakt lokal)"}

def fetch(title):
    url = BASE + urllib.parse.quote(title.replace(" ", "_"))
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise
    except Exception:
        return None, None

def is_disambig(soup):
    # Begriffsklaerung: Kategorie-Link oder typische Struktur
    for a in soup.select("#catlinks a, .catlinks a"):
        if "Begriffsklärung" in a.get_text():
            return True
    return False

def _clean(p):
    for bad in p.select("sup, .mw-editsection, style"):
        bad.decompose()
    t = p.get_text(" ", strip=True)
    t = re.sub(r"\[\d+\]", "", t)               # [1]-Fussnoten
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)      # Leerzeichen vor Satzzeichen (Link+Punkt)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_intro(html, max_chars=1500):
    soup = BeautifulSoup(html, "lxml")
    if is_disambig(soup):
        return None, True
    paras = []
    # Anker 1: "Kurzbeschreibung"-Abschnitt (Standard bei Spezies/Kultur/Profession)
    anchor = soup.find(id="Kurzbeschreibung")
    if anchor:
        wrap = anchor.find_parent(class_="mw-heading") or anchor
        sib = wrap
        while True:
            sib = sib.find_next_sibling()
            if sib is None:
                break
            cls = sib.get("class") or []
            if sib.name in ("h2", "h3") or "mw-heading" in cls:
                break
            if sib.name == "p":
                paras.append(sib)
    # Anker 2 (Fallback): Intro-Absaetze vor der ersten Ueberschrift
    if not paras:
        for out in soup.select(".mw-parser-output"):
            buf = []
            for el in out.find_all(recursive=False):
                cls = el.get("class") or []
                if el.name in ("h2", "h3") or "mw-heading" in cls:
                    break
                if el.name == "p":
                    buf.append(el)
            if buf:
                paras = buf
                break
    parts = [t for t in (_clean(p) for p in paras) if t]
    text = " ".join(parts).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        if "." in cut[-220:]:
            cut = cut[:cut.rfind(".") + 1]
        text = cut
    return (text or None), False

API = "https://de.wiki-aventurica.de/de/api.php"

def opensearch(term, limit=5):
    try:
        u = API + "?" + urllib.parse.urlencode({"action": "opensearch", "search": term, "limit": limit, "format": "json"})
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return d[1] if isinstance(d, list) and len(d) > 1 else []
    except Exception:
        return []

def similar(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

SPEZIES_LEMMA = {"Mensch": ["Menschen"], "Elf": ["Elfen"], "Halbelf": ["Halbelfen"], "Zwerg": ["Zwerge"],
                 "Achaz": ["Achaz"], "Goblin": ["Goblins", "Goblin"], "Ork": ["Orks", "Ork"],
                 "Halbork": ["Halbork", "Halborks", "Halb-Ork"]}

def candidates(name, kind):
    base = re.sub(r"\s*\(.*?\)\s*", "", name).strip()   # Klammerzusatz entfernen
    c = []
    if kind == "spezies":
        c += SPEZIES_LEMMA.get(name, [name])
    if kind == "kulturen":
        c += [name + " (Kultur)", base + " (Kultur)", name, base]
    if kind == "professionen":
        c += [name]
        if name.endswith("hexer"): c.append(name[:-2] + "e")     # Krötenhexer -> Krötenhexe
        if name.endswith("geweihter"):                            # Praiosgeweihter -> Praios-Geweihter etc.
            st = name[:-len("geweihter")]
            c += [st + "-Geweihter", st + "-Geweihte", "Geweihter des " + st,
                  "Geweihte der " + st, st + "geweihte"]
        if name.endswith("er"):    c.append(name[:-2] + "in")    # Wildnisläufer -> ...läuferin (Redirect)
        if name.endswith("in"):    c.append(name[:-2])           # feminin -> maskulin
        c += {"Prostituierter": ["Prostituierte", "Hure"], "Adliger": ["Adel"],
              "Namenloser-Geweihter": ["Geweihter des Namenlosen", "Namenlosen-Geweihter"],
              "Numinorupriester": ["Geweihter des Numinoru", "Numinoru"],
              "Sumudiener": ["Diener des Sumu", "Sumu"]}.get(name, [])
        c += [name + " (Profession)", base]
    seen, out = set(), []
    for x in c:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def resolve(name, kind, max_chars=1500):
    """Loest einen Namen auf: Kandidaten-Lemmata, dann opensearch-Fallback."""
    cands = candidates(name, kind)
    # 1) direkte Kandidaten
    for cand in cands:
        html, finalurl = fetch(cand)
        time.sleep(0.35)
        if not html:
            continue
        text, disamb = extract_intro(html, max_chars)
        if disamb or not text or len(text) < 25:
            continue
        lemma = urllib.parse.unquote(finalurl.split("/wiki/")[-1]).replace("_", " ") if finalurl else cand
        return lemma, text
    # 2) opensearch: erster Treffer, der dem Namen aehnlich genug ist
    for hit in opensearch(name):
        if similar(name, hit) < 0.6 and not hit.lower().startswith(name.lower()[:6]):
            continue
        html, finalurl = fetch(hit)
        time.sleep(0.35)
        if not html:
            continue
        text, disamb = extract_intro(html, max_chars)
        if disamb or not text or len(text) < 25:
            continue
        return hit, text
    return None, None

def load_names():
    dj = open("dsa-daten.js", encoding="utf-8").read()
    dj = dj[dj.index("{"):dj.rindex("}") + 1]
    D = json.loads(dj)
    spez, kult = ["Mensch", "Halbelf", "Elf", "Zwerg"], list(D["KULTUREN"].keys())
    try:  # Erweiterungs-Spezies/-Kulturen aus dsa-exoten.js mitnehmen
        ej = open("dsa-exoten.js", encoding="utf-8").read()
        EX = json.loads(ej[ej.index("{"):ej.rindex("}") + 1])
        spez += list(EX.get("SPEZIES", {}).keys())
        kult += [k for k in EX.get("KULTUREN", {}).keys() if k not in kult]
        exprof = list(EX.get("PROFESSIONEN", {}).keys())
    except Exception:
        exprof = []
    return {"spezies": spez, "kulturen": kult,
            "professionen": list(D["PROFESSIONEN"].keys()) + exprof}

def run():
    names = load_names()
    # Resume: vorhandene dsa-lore.json laden, schon Gescrapte ueberspringen
    out = {"spezies": {}, "kulturen": {}, "professionen": {}}
    try:
        out.update(json.load(open("dsa-lore.json", encoding="utf-8")))
    except Exception:
        pass
    for kind in ("spezies", "kulturen", "professionen"):
        cap = 2000 if kind != "professionen" else 700   # Professionen kurz, Spezies/Kultur ausfuehrlicher
        todo = [n for n in names[kind] if n not in out.get(kind, {})]
        print(f"== {kind}: {len(todo)} offen / {len(names[kind])} gesamt", flush=True)
        for i, name in enumerate(todo, 1):
            lemma, text = resolve(name, kind, cap)
            if text:
                out[kind][name] = {"lemma": lemma, "text": text}
                print(f"  [{i}/{len(todo)}] OK  {name}  ({len(text)} Z., <- {lemma})", flush=True)
            else:
                print(f"  [{i}/{len(todo)}] --  {name}  KEIN TREFFER", flush=True)
            if i % 10 == 0:   # Zwischenstand sichern
                json.dump(out, open("dsa-lore.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(out, open("dsa-lore.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # Coverage-Report
    print("\n==== COVERAGE ====")
    for kind in ("spezies", "kulturen", "professionen"):
        have = len(out[kind]); total = len(names[kind])
        miss = [n for n in names[kind] if n not in out[kind]]
        print(f"{kind}: {have}/{total}")
        if miss:
            print("   FEHLT:", ", ".join(miss[:40]) + (" …" if len(miss) > 40 else ""))

if __name__ == "__main__":
    if "--test" in sys.argv:
        for kind, name in [("spezies", "Zwerg"), ("kulturen", "Thorwaler"),
                            ("kulturen", "Mittelreicher"), ("professionen", "Krötenhexer"),
                            ("professionen", "Katzenhexer"), ("professionen", "Dajin-Buskur"),
                            ("professionen", "Streuner")]:
            lemma, text = resolve(name, kind, 700)
            print(f"\n## {name} ({kind}) -> {lemma!r}\n{(text or '<<KEIN TEXT>>')[:300]}")
    else:
        run()
