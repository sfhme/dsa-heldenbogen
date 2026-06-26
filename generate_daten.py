"""Erzeugt dsa-daten.js (window.DSADATEN) aus der Optolith-Datenbank (optolith-data/).
Join: data_univ/<X>.yaml (Zahlen) + data_de/<X>.yaml (Namen) über die id.
Aufruf:  python generate_daten.py
"""
import yaml, json

D = "optolith-data"
def U(f):  return yaml.safe_load(open(f"{D}/data_univ/{f}.yaml", encoding="utf-8"))
def DEm(f): return {e["id"]: e for e in yaml.safe_load(open(f"{D}/data_de/{f}.yaml", encoding="utf-8"))}

ATTR = {f"ATTR_{i}": s for i, s in enumerate(["MU","KL","IN","CH","FF","GE","KO","KK"], 1)}
SOZ  = {1:"Unfrei", 2:"Frei", 3:"Niederadel", 4:"Adel", 5:"Hochadel"}
REACH= {1:"kurz", 2:"mittel", 3:"lang"}
RACE_SPEZIES = {"R_1":"Mensch","R_2":"Elf","R_3":"Halbelf","R_4":"Zwerg"}

def nameval(v):
    if isinstance(v, dict): return v.get("m") or v.get("f") or next(iter(v.values()), "")
    return v or ""

skN = {i:nameval(e.get("name")) for i,e in DEm("Skills").items()}
skSF = {skN[s["id"]]: s.get("ic") for s in U("Skills") if s.get("id") in skN}   # Talent -> Steigerungsfaktor A/B/C/D
ctN = {i:nameval(e.get("name")) for i,e in DEm("CombatTechniques").items()}
ctSF = {ctN[c["id"]]: c.get("ic") for c in U("CombatTechniques") if c.get("id") in ctN}   # Kampftechnik -> SF
spN = {i:nameval(e.get("name")) for i,e in DEm("Spells").items()};            deSp = DEm("Spells")
spSF = {spN[s["id"]]: s.get("ic") for s in U("Spells") if spN.get(s["id"])}                # Zauber -> SF A/B/C/D
liN = {i:nameval(e.get("name")) for i,e in DEm("LiturgicalChants").items()};  deLi = DEm("LiturgicalChants")
liSF = {liN[s["id"]]: s.get("ic") for s in U("LiturgicalChants") if liN.get(s["id"])}      # Liturgien -> SF
adN = {i:nameval(e.get("name")) for i,e in DEm("Advantages").items()}
diN = {i:nameval(e.get("name")) for i,e in DEm("Disadvantages").items()}
eqN = {i:nameval(e.get("name")) for i,e in DEm("Equipment").items()}
pvN = {i:nameval(e.get("name")) for i,e in DEm("ProfessionVariants").items()}
cuN = {i:nameval(e.get("name")) for i,e in DEm("Cultures").items()}
prN = {i:nameval(e.get("name")) for i,e in DEm("Professions").items()}
saN = {i:nameval(e.get("name")) for i,e in DEm("SpecialAbilities").items()}
_saU = {s["id"]: s for s in U("SpecialAbilities")}
def sa_cost(sa_id, level=None):
    s = _saU.get(sa_id, {}); c = s.get("cost")
    if isinstance(c, list):
        idx = (level or 1) - 1
        return c[min(idx, len(c)-1)]
    return c or 0
cuDE = DEm("Cultures")

def probe(u): return [ATTR[u["check1"]], ATTR[u["check2"]], ATTR[u["check3"]]]
def cost_str(c):
    if c is None: return ""
    if isinstance(c, list): return "/".join(str(x) for x in c)
    return str(c)
def tp(sp):
    s = sp.get("damageDiceSides")
    if not s: return ""
    base = f"{sp.get('damageDiceNumber',1) or 1}W{s}"
    f = sp.get("damageFlat", 0) or 0
    return base + (f"+{f}" if f > 0 else (str(f) if f < 0 else ""))
def names(lst, nm):
    out = []
    for x in (lst or []):
        xid = x.get("id") if isinstance(x, dict) else x
        if isinstance(xid, list): continue          # Auswahl-Option -> überspringen
        n = nm.get(xid)
        if n: out.append(n)
    return out
def paket(lst, nm):
    out = []
    for x in (lst or []):
        if not isinstance(x, dict): continue
        xid = x.get("id")
        if isinstance(xid, list):                   # Auswahl-Option -> als Wahl exportieren
            choices = [nm[i] for i in xid if i in nm]
            if choices: out.append({"wahl": choices, "value": x.get("value")})
        elif xid in nm:
            out.append({"name": nm[xid], "value": x.get("value")})
    return out

O = {}
O["ZAUBER"] = sorted([{"name":spN[u["id"]], "probe":probe(u),
    "kosten":deSp[u["id"]].get("aeCostShort") or "", "rw":deSp[u["id"]].get("rangeShort") or "",
    "dauer":deSp[u["id"]].get("durationShort") or ""} for u in U("Spells") if spN.get(u["id"])],
    key=lambda x:x["name"])
O["LITURGIEN"] = sorted([{"name":liN[u["id"]], "probe":probe(u),
    "kosten":deLi[u["id"]].get("kpCostShort") or "", "rw":deLi[u["id"]].get("rangeShort") or "",
    "dauer":deLi[u["id"]].get("durationShort") or ""} for u in U("LiturgicalChants") if liN.get(u["id"])],
    key=lambda x:x["name"])
O["VORTEILE"]  = sorted([{"name":adN[u["id"]], "ap":cost_str(u.get("cost"))} for u in U("Advantages") if adN.get(u["id"])], key=lambda x:x["name"])
O["NACHTEILE"] = sorted([{"name":diN[u["id"]], "ap":cost_str(u.get("cost"))} for u in U("Disadvantages") if diN.get(u["id"])], key=lambda x:x["name"])
O["KAMPFTECHNIKEN"] = [{"name":ctN[u["id"]],
    "leit":[ATTR[a] for a in (u["primary"] if isinstance(u.get("primary"),list) else [u.get("primary")]) if a],
    "fern":u.get("gr")==2} for u in U("CombatTechniques") if ctN.get(u["id"])]

nah=[]; fern=[]; ruest=[]
for u in U("Equipment"):
    sp = u.get("special") or {}; nm = eqN.get(u["id"])
    if not nm: continue
    if u.get("gr")==1 and sp.get("combatTechnique"):
        nah.append({"name":nm, "technik":ctN.get(sp["combatTechnique"],""), "tp":tp(sp),
                    "at":sp.get("at",0), "pa":sp.get("pa",0), "rw":REACH.get(sp.get("reach"),"")})
    elif u.get("gr")==2 and sp.get("combatTechnique"):
        nah_rng = f"{sp.get('closeRange','')}/{sp.get('mediumRange','')}/{sp.get('farRange','')}"
        fern.append({"name":nm, "technik":ctN.get(sp["combatTechnique"],""), "tp":tp(sp),
                     "lz":sp.get("reloadTime",""), "rw":nah_rng})
    elif u.get("gr")==4 and "protection" in sp:
        ruest.append({"name":nm, "rs":sp.get("protection",0), "be":sp.get("encumbrance",0)})
O["WAFFEN_NAH"]  = sorted(nah,  key=lambda x:x["name"])
O["WAFFEN_FERN"] = sorted(fern, key=lambda x:x["name"])
O["RUESTUNGEN"]  = sorted(ruest,key=lambda x:x["name"])

# --- Kultur→Profession-Filter: typische Professionen je Kultur ---
# weltlich exakt aus den Strukturdaten (commonMundaneProfessionsAll/Exceptions, saubere P-IDs),
# magisch/geweiht aus den de-Regelbuch-Texten (commonMagical/BlessedProfessions) über Oberbegriffe,
# weil deren Strukturdaten gemischt/integer-kodiert und nicht verlässlich auflösbar sind.
import re as _re
GR_NAMES = {1: set(), 2: set(), 3: set()}
for _u in U("Professions"):
    _n = prN.get(_u["id"]); _g = _u.get("gr")
    if _n and _g in GR_NAMES:
        GR_NAMES[_g].add(_n)
def _pid_name(pid): return prN.get(pid)
def _terms(text):
    out = []
    for raw in _re.split(r"[,/]", text or ""):
        t = _re.sub(r"\(.*?\)", "", raw)
        t = _re.sub(r"\b(selten|sehr|vor allem)\b", "", t, flags=_re.I).strip()
        if t:
            out.append(t)
    return out
_MAG = [
    ("magier", lambda n: "magier" in n.lower() and "sexual" not in n.lower()),
    ("hexe", lambda n: n in ("Katzenhexer", "Krötenhexer", "Rabenhexer")),
    ("druide", lambda n: "druide" in n.lower()),
    ("wildnisläufer", lambda n: "wildnisläufer" in n.lower()),
    ("zauberweber", lambda n: "zauberweber" in n.lower()),
    ("schelm", lambda n: "schelm" in n.lower()),
    ("scharlatan", lambda n: "scharlatan" in n.lower()),
    ("geode", lambda n: "geode" in n.lower()),
    ("sexualmagier", lambda n: "sexualmagier" in n.lower()),
    ("zaubertänzer", lambda n: n.lower() in ("hazaqi", "sharisad", "sangara")),
]
def resolve_mundane(u):
    allf = u.get("commonMundaneProfessionsAll")
    exc = {_pid_name(x) for x in (u.get("commonMundaneProfessionsExceptions") or [])
           if isinstance(x, str) and _pid_name(x)}
    return sorted(GR_NAMES[1] - exc if allf else exc)
def resolve_magic(text):
    out = set()
    for term in _terms(text):
        tl = term.lower(); hit = False
        for key, pred in _MAG:
            if key in tl:
                out |= {n for n in GR_NAMES[2] if pred(n)}; hit = True
        if not hit:
            out |= {n for n in GR_NAMES[2] if tl in n.lower()}
    return sorted(out)
def resolve_blessed(text):
    out = set()
    for term in _terms(text):
        god = term.lower().split("gewei")[0].split("priester")[0].strip()
        if god:
            out |= {n for n in GR_NAMES[3] if god in n.lower()}
    return sorted(out)

cult = {}
for u in U("Cultures"):
    nm = cuN.get(u["id"])
    if not nm: continue
    cult[nm] = {
        "social": [SOZ[s] for s in (u.get("social") or []) if s in SOZ],
        "common": names(u.get("commonSkills"), skN),
        "uncommon": names(u.get("uncommonSkills"), skN),
        "paket": paket(u.get("culturalPackageSkills"), skN),
        "commonVorteile": names(u.get("commonAdvantages"), adN),
        "commonNachteile": names(u.get("commonDisadvantages"), diN),
        "profWeltlich": resolve_mundane(u),
        "profMagisch": resolve_magic((cuDE.get(u["id"]) or {}).get("commonMagicalProfessions")),
        "profGeweiht": resolve_blessed((cuDE.get(u["id"]) or {}).get("commonBlessedProfessions")),
    }
O["KULTUREN"] = cult

prof = {}
for u in U("Professions"):
    nm = prN.get(u["id"])
    if not nm: continue
    _sel = u.get("combatTechniqueSelectOptions")
    _wahl = ({"amount": _sel.get("amount", 1), "value": _sel.get("value", 0),
               "aus": [ctN[c] for c in (_sel.get("sid") or []) if c in ctN]}
             if _sel and _sel is not False else None)
    _rd = u.get("raceDependency")
    prof[nm] = {
        "cost": u.get("cost"),
        "gr": u.get("gr"),
        "sgr": u.get("sgr"),
        "rassenReq": RACE_SPEZIES.get(_rd) if isinstance(_rd, str) else None,
        "variantePflicht": bool(u.get("isVariantRequired")),
        "talente": paket(u.get("skills"), skN),
        "kampftechniken": paket(u.get("combatTechniques"), ctN),
        "wahlKT": _wahl,                                   # Wahl-Kampftechnik falls vorhanden
        "sf": [{"name": saN[s["id"]], "ap": sa_cost(s["id"], s.get("level")), "stufe": s.get("level")}
               for s in (u.get("specialAbilities") or []) if s.get("id") in saN],
        "zauber": paket(u.get("spells"), spN),
        "liturgien": paket(u.get("liturgicalChants"), liN),
        "varianten": names(u.get("variants"), pvN),
        "vorteile": names(u.get("suggestedAdvantages"), adN),
    }
O["PROFESSIONEN"] = prof

# Professionsvarianten: Talent-/Technik-Modifikationen (Deltas auf das Basis-Paket)
varianten = {}
for v in U("ProfessionVariants"):
    nm = pvN.get(v["id"])
    if not nm:
        continue
    _vsel = v.get("combatTechniqueSelectOptions")
    varianten[nm] = {
        "talente": [{"name": skN[s["id"]], "value": s.get("value")}
                    for s in (v.get("skills") or []) if isinstance(s, dict) and s.get("id") in skN],
        "kampftechniken": [{"name": ctN[c["id"]], "value": c.get("value")}
                           for c in (v.get("combatTechniques") or []) if isinstance(c, dict) and c.get("id") in ctN],
        "sfAend": [{"name": saN[s["id"]], "aktiv": s.get("active", True),
                    "ap": sa_cost(s["id"], s.get("level")), "stufe": s.get("level")}
                   for s in (v.get("specialAbilities") or []) if isinstance(s, dict) and s.get("id") in saN],
        "wahlKTEntfernt": _vsel is False,                  # True wenn Variante Wahl-KT der Basis entfernt
        "cost": v.get("cost"),
    }
O["VARIANTEN"] = varianten

# Aussehen je Kultur: Größe/Gewicht-Würfel + typische Haar-/Augenfarbe (aus RaceVariants + Races)
from collections import Counter as _Counter
hairN = {i: nameval(e.get("name")) for i, e in DEm("HairColors").items()}
eyeN = {i: nameval(e.get("name")) for i, e in DEm("EyeColors").items()}
rv_to_race = {}
for r in U("Races"):
    for vid in (r.get("variants") or []):
        rv_to_race[vid] = r
def _names(idxs, tab):
    # gewichtete Farb-Liste (Optolith-Tabelle: haeufige Farben mehrfach -> beim Wuerfeln wahrscheinlicher)
    return [tab[i] for i in (idxs or []) if i in tab]
aussehen = {}
for rv in U("RaceVariants"):
    race = rv_to_race.get(rv["id"]) or {}
    haar = _names(rv.get("hairColors"), hairN)
    augen = _names(rv.get("eyeColors"), eyeN)
    for cid in (rv.get("commonCultures") or []):
        cn = cuN.get(cid)
        if not cn:
            continue
        aussehen[cn] = {"sizeBase": rv.get("sizeBase"), "sizeDice": rv.get("sizeRandom") or [],
                        "weightBase": race.get("weightBase"), "weightDice": race.get("weightRandom") or [],
                        "haar": haar, "augen": augen}
O["TALENT_SF"] = skSF
O["KT_SF"] = ctSF
O["ZAUBER_SF"] = spSF
O["LITURGIEN_SF"] = liSF
O["AUSSEHEN"] = aussehen
# Spezies-Fallback: Kulturen ohne eigene RaceVariant (z.B. alle Zwerge, Halbelfen, seltene Menschen-Kulturen)
aussehen_spz = {}
for r in U("Races"):
    sn = RACE_SPEZIES.get(r["id"])
    if not sn:
        continue
    rvs = [rv for rv in U("RaceVariants") if rv["id"] in (r.get("variants") or [])]
    sizeBase, sizeDice = r.get("sizeBase"), r.get("sizeRandom") or []
    if sizeBase is None and rvs:  # Mensch: Groesse steckt in den Varianten -> Mittelwert
        sizeBase = round(sum(rv.get("sizeBase", 0) for rv in rvs) / len(rvs))
        sizeDice = rvs[0].get("sizeRandom") or []
    hc = list(r.get("hairColors") or [])
    ec = list(r.get("eyeColors") or [])
    if not hc:
        for rv in rvs: hc += (rv.get("hairColors") or [])
    if not ec:
        for rv in rvs: ec += (rv.get("eyeColors") or [])
    aussehen_spz[sn] = {"sizeBase": sizeBase, "sizeDice": sizeDice,
                        "weightBase": r.get("weightBase"), "weightDice": r.get("weightRandom") or [],
                        "haar": _names(hc, hairN), "augen": _names(ec, eyeN)}
O["AUSSEHEN_SPEZIES"] = aussehen_spz

js = "window.DSADATEN = " + json.dumps(O, ensure_ascii=False) + ";\n"
open("dsa-daten.js", "w", encoding="utf-8").write(js)
print("dsa-daten.js geschrieben.")
for k in O:
    v = O[k]
    print(f"  {k}: {len(v)}")
# Stichproben
ig = next((z for z in O["ZAUBER"] if z["name"]=="Ignifaxius"), None)
print("Stichprobe Ignifaxius:", ig)
print("Stichprobe Kultur Mittelreicher:", {k:O['KULTUREN'].get('Mittelreicher',{}).get(k) for k in ('social','common','paket')})
print("Stichprobe Profession Amazone Varianten:", O['PROFESSIONEN'].get('Amazone',{}).get('varianten'))
