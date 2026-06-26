# -*- coding: utf-8 -*-
"""Erzeugt dsa-exoten.js (window.DSAEXOTEN) = spielbare Erweiterungs-Spezies (Achaz/Goblin/Ork/
Halbork) + ihre Kulturen, aus Kurts Regelwiki-Korpus (Primärquelle). Spezies-Werte hand-definiert
(gegen den Korpus verifiziert), Kulturen geparst. Im Bogen hinter dem 'Regeln ignorieren'-Toggle.
"""
import json, re

CORPUS = r"D:\Claude\kurt\data\dsa_corpus.jsonl"
ROWS = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
TXT = {(r.get("titel") or ""): (r.get("text") or "") for r in ROWS}

# ---- Spezies (Werte aus dem Regelwiki-Korpus verifiziert) ----------------------------------
SPEZIES = {
    "Achaz":   {"lep": 5, "sk": -4, "zk": -5, "gs": 8},
    "Goblin":  {"lep": 3, "sk": -6, "zk": -5, "gs": 8},
    "Ork":     {"lep": 8, "sk": -6, "zk": -4, "gs": 8},
    "Halbork": {"lep": 6, "sk": -6, "zk": -5, "gs": 8},
}
SPEZ_AP = {"Achaz": 25, "Goblin": 5, "Ork": 18, "Halbork": 1}
# fix = feste Mods, minus2 = Auswahl (eine davon), minusVal = Betrag des Minus (Exoten: 1)
SPEZ_MOD = {
    "Achaz":   {"fix": {"IN": 1, "KO": 1}, "frei1": False, "minus2": ["MU", "KK"], "minusVal": 1},
    "Goblin":  {"fix": {"FF": 1, "GE": 1}, "frei1": False, "minus2": ["MU", "KL"], "minusVal": 1},
    "Ork":     {"fix": {"MU": 1, "KO": 1}, "frei1": False, "minus2": ["KL", "CH"], "minusVal": 1},
    "Halbork": {"fix": {"KO": 1, "CH": -1}, "frei1": False, "minus2": None, "minusVal": 1},
}
SPEZ_AUTO = {
    "Achaz":   "Dunkelsicht I, Zusätzliche Gliedmaße (Schwanz); Nachteil: Kältestarre",
    "Goblin":  "Dunkelsicht I, Herausragender Sinn (Gehör), Herausragender Sinn (Geruch & Geschmack), Krankheitsresistenz I",
    "Ork":     "—",
    "Halbork": "Zäher Hund",
}
# Spezies -> übliche Kulturen. Region-Referenzen (Svellttal/Thorwal/Bornland/Nordaventurien) gibt es
# nicht als eigene Exoten-Seiten -> auf die bestehenden Menschen-Kulturen gemappt (Orks/Goblins dort).
SPEZ_KULT = {
    "Achaz":   ["Stammesachaz", "Achaz-Rha", "Ctki'Ssrr"],
    "Goblin":  ["Räuberbande", "Bornländer", "Nordaventurier"],
    "Ork":     ["Orkland", "Räuberbande", "Svellttaler", "Thorwaler"],
    "Halbork": ["Orkland", "Räuberbande", "Svellttaler", "Thorwaler"],
}
# Nur diese Kulturen sind NEU (nicht in dsa-daten.js) und müssen geparst werden:
NEU_KULT = ["Stammesachaz", "Achaz-Rha", "Ctki'Ssrr", "Orkland", "Räuberbande", "Utulus", "Waldmenschen"]

SOZ = ("Unfrei", "Frei", "Niederadel", "Adel", "Hochadel")

def find_title(name):
    """Korpus-Titel finden (toleriert Apostroph-Varianten wie Ctki'Ssrr)."""
    if name in TXT:
        return name
    norm = lambda s: re.sub(r"[’'`´]", "'", s)
    for t in TXT:
        if norm(t) == norm(name):
            return t
    return None

def field_line(txt, label):
    """Wert hinter 'Label\\n: …' (eine Zeile)."""
    m = re.search(re.escape(label) + r"\s*\n\s*:\s*([^\n]*)", txt)
    return m.group(1).strip() if m else ""

def proflist(s):
    s = (s or "").replace("–", "").replace("—", "").strip()
    out = []
    for p in s.split(","):
        p = p.strip()
        # Klammerzusätze wie "Seefahrer (Fischer)" behalten, leere/Strich raus
        if p and p not in ("", "-", "·"):
            out.append(p)
    return out

def parse_kultur(name):
    t = find_title(name)
    if not t:
        return None
    txt = TXT[t]
    soz = field_line(txt, "Sozialstatus")
    social = [s for s in (x.strip() for x in re.split(r"[,/]", soz)) if s in SOZ]
    welt = field_line(txt, "Weltliche Professionen") or field_line(txt, "Weltliche Profession")
    mag = field_line(txt, "Zaubererprofessionen") or field_line(txt, "Zaubererprofession")
    gew = field_line(txt, "Geweihtenprofessionen") or field_line(txt, "Geweihtenprofession")
    return {"social": social or list(SOZ), "profWeltlich": proflist(welt),
            "profMagisch": proflist(mag), "profGeweiht": proflist(gew), "_lemma": t}

# ---- exotische Professionen (race/kultur-gesperrt, nicht in den 180) -------------------------
# bekannte Talent-/Kampftechnik-Namen aus dsa-daten.js -> robustes Matching (kein Müll)
_D = json.loads((lambda s: s[s.index("{"):s.rindex("}") + 1])(open("dsa-daten.js", encoding="utf-8").read()))
TAL_NAMEN = sorted([t["name"] for t in (_D.get("TALENTE_LISTE") or [])] or list(_D.get("TALENTE", {}).keys()) or
                   [t for grp in _D.get("TALENTE_KAT", {}).values() for t in grp], key=len, reverse=True)
if not TAL_NAMEN:  # Fallback: aus PROFESSIONEN-Paketen sammeln
    s = set()
    for p in _D["PROFESSIONEN"].values():
        for t in (p.get("talente") or []): s.add(t["name"])
    TAL_NAMEN = sorted(s, key=len, reverse=True)
KT_NAMEN = sorted([k["name"] for k in _D.get("KAMPFTECHNIKEN", [])], key=len, reverse=True)

PROF_NEU = ["Echsenreiter", "Achazschamane", "Chr'Ssir'Ssr-Priester", "Graveshpriester",
            "Rikaipriester", "Tairachschamane", "Tairachgeweihter", "Räuberin"]

def parse_profession(name):
    t = find_title(name)
    if not t:
        return None
    txt = TXT[t]
    m = re.search(r"AP-Wert\s*\n?\s*:?\s*(\d+)", txt)
    if not m:
        return None
    cost = int(m.group(1))
    vor = field_line(txt, "Voraussetzungen")
    gr = 3 if "Geweihter" in vor or "schamane" in name.lower() or "priester" in name.lower() else (2 if "Zauberer" in vor else 1)
    rd = re.search(r"Spezies\s+([A-Za-zÄÖÜäöü]+)", vor)
    cd = re.search(r"Kultur\s+([A-Za-zÄÖÜäöü'\- ]+?)(?:,|\bVorteil|\bNachteil|$)", vor)
    ktline = field_line(txt, "Kampftechniken")
    kt = [{"name": kn, "value": int(mm.group(1))} for kn in KT_NAMEN
          for mm in [re.search(re.escape(kn) + r"\s+(\d+)", ktline)] if mm]
    talsec = txt[txt.find("Talente"):] if "Talente" in txt else ""
    cut = min([i for i in (talsec.find("Ausrüstung"), talsec.find("Startkapital"), 1800) if i > 0] or [1800])
    talsec = talsec[:cut]
    tal = [{"name": tn, "value": int(mm.group(1))} for tn in TAL_NAMEN
           for mm in [re.search(r"(?<![\wäöüß])" + re.escape(tn) + r"\s+(\d+)", talsec)] if mm]
    spez_map = {"Achaz": "Achaz", "Goblins": "Goblin", "Goblin": "Goblin", "Orks": "Ork", "Ork": "Ork", "Halbork": "Halbork"}
    return {"cost": cost, "gr": gr, "sgr": (2 if any(w in name for w in ("krieger", "reiter", "Krieger")) else 1),
            "raceDependency": spez_map.get(rd.group(1)) if rd else None,
            "cultureDependency": cd.group(1).strip() if cd else None,
            "talente": tal, "kampftechniken": kt, "varianten": [], "_lemma": t}

if __name__ == "__main__":
    KULTUREN, missing = {}, []
    for k in NEU_KULT:
        d = parse_kultur(k)
        if d:
            KULTUREN[k] = {kk: vv for kk, vv in d.items() if kk != "_lemma"}
        else:
            missing.append(k)
    # Mohas-Verwandte (Menschen) sollen zusätzlich im Mensch-Dropdown auftauchen
    extra_mensch = [k for k in ("Utulus", "Waldmenschen") if k in KULTUREN]

    # exotische Professionen parsen
    PROFESSIONEN, prof_missing = {}, []
    for p in PROF_NEU:
        d = parse_profession(p)
        if d:
            PROFESSIONEN[p] = {k: v for k, v in d.items() if k != "_lemma"}
        else:
            prof_missing.append(p)

    out = {"SPEZIES": SPEZIES, "SPEZ_AP": SPEZ_AP, "SPEZ_MOD": SPEZ_MOD,
           "SPEZ_AUTO": SPEZ_AUTO, "SPEZ_KULT": SPEZ_KULT,
           "KULTUREN": KULTUREN, "EXTRA_KULT_MENSCH": extra_mensch,
           "PROFESSIONEN": PROFESSIONEN}
    with open("dsa-exoten.js", "w", encoding="utf-8") as f:
        f.write("window.DSAEXOTEN = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")

    print("NEUE Kulturen:", list(KULTUREN.keys()), "| fehlend:", missing)
    print("NEUE Professionen:", list(PROFESSIONEN.keys()), "| fehlend:", prof_missing)
    print("Bekannte Talentnamen:", len(TAL_NAMEN), "| Kampftechniken:", len(KT_NAMEN))
    for p, v in PROFESSIONEN.items():
        print(f"  {p}: gr{v['gr']} {v['cost']}AP race={v['raceDependency']} kult={v['cultureDependency']} | {len(v['talente'])} Talente, {len(v['kampftechniken'])} Kampft.")
