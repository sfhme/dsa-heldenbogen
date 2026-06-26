"""Parst die 6 vorgefertigten Helden aus den DSA-Schnellstartregeln (Seiten 15-20)
und schreibt dsa-pregens.js (window.DSAPREGENS). Werte werden danach gegen die
bekannten PDF-Angaben verifiziert."""
import fitz, json, re

doc = fitz.open("referenz_schnellstart.pdf")
ATTRS = [("Mut","MU"),("Klugheit","KL"),("Intuition","IN"),("Charisma","CH"),
         ("Fingerfertigkeit","FF"),("Gewandtheit","GE"),("Konstitution","KO"),("Körperkraft","KK")]
LABELS = ["Vorteile","Nachteile","Sonderfertigkeiten","Sprachen","Schriften",
          "Kampftechniken","Talente","Zauber","Ausrüstung","Spezies","Kultur","Profession","Erfahrungsgrad"]

def first(rx, t, d=None, g=1):
    m = re.search(rx, t, re.S); return m.group(g).strip() if m else d

def parse(t):
    t = re.sub(r"-\n\s*", "", t)   # Silbentrennung am Zeilenende auflösen
    h = {}
    h["spezies"]    = first(r"Spezies:\s*([^\n]+)", t, "")
    h["spezies"]    = next((s for s in ["Halbelf","Mensch","Elf","Zwerg"] if s in h["spezies"]), h["spezies"])
    h["kultur"]     = first(r"Kultur:\s*([^\n]+)", t, "")
    h["profession"] = first(r"Profession:\s*([^\n]+)", t, "")
    head = t[:t.find("Vorteile")] if "Vorteile" in t else t
    h["eig"] = {}
    for name, short in ATTRS:
        m = re.search(rf"{name}\s*\n?\s*(\d+)", head); h["eig"][short] = int(m.group(1)) if m else 0
    h["lep"]   = int(first(r"Lebenspunkte\s*\n?\s*(\d+)", t, "0"))
    a = first(r"Astralpunkte\s*\n?\s*(\d+)", t); h["asp"] = int(a) if a else 0
    h["schips"]= int(first(r"Schips\s*\n?\s*(\d+)", t, "0"))
    # Freitext-Listen bis zum nächsten Label
    stop = "|".join(LABELS)
    for key, lab in [("vorteile","Vorteile"),("nachteile","Nachteile"),("sonderf","Sonderfertigkeiten"),
                     ("sprachen","Sprachen"),("schriften","Schriften")]:
        m = re.search(rf"{lab}:\s*(.+?)(?:\n(?:{stop}):)", t, re.S)
        h[key] = re.sub(r"\s+"," ", m.group(1)).strip() if m else ""
    # Kampftechniken: "Name N (AT X / PA Y)" oder "(FK Z)"
    kt = {}
    block = first(r"Kampftechniken:\s*(.+?)(?:\n(?:Talente|Ausrüstung|Zauber):)", t)
    if block:
        for mm in re.finditer(r"([A-Za-zÄÖÜäöüß& ]+?)\s+(\d+)\s*\(\s*(AT|FK)\s*(\d+)\s*(?:/\s*PA\s*([\d–\-]+))?\s*\)", block):
            kt[mm.group(1).strip()] = {"ktw":int(mm.group(2)), "at":mm.group(4) if mm.group(3)=="AT" else "",
                                       "fk":mm.group(4) if mm.group(3)=="FK" else "", "pa":(mm.group(5) or "").replace("–","")}
    h["kampftechniken"] = kt
    # Talente: 5 Gruppenzeilen "Gruppe (Probe): Name N, Name N, ..."
    tal = {}
    talblock = first(r"Talente:\s*(.+?)(?:\n(?:Zauber|Ausrüstung):)", t)
    if talblock:
        for line in re.split(r"(?:Körper|Gesellschaft|Natur|Wissen|Handwerk)\s*\([^)]*\)\s*:", talblock):
            for item in line.split(","):
                m = re.match(r"\s*([A-Za-zÄÖÜäöüß&\- ]+?)\s+(\d+)\s*$", item.strip())
                if m and int(m.group(2)) > 0: tal[m.group(1).strip()] = int(m.group(2))
    h["talente"] = tal
    # Zauber: "Name (Probe) FW"
    z = []
    zblock = first(r"\nZauber:\s*(.+?)(?:\n(?:Ausrüstung|Spezies):)", t)
    if zblock:
        for zm in re.finditer(r"([A-Za-zÄÖÜäöüß ]+?)\s*\(([^)]+)\)\s*(\d+)", zblock):
            z.append({"name":zm.group(1).strip(), "probe":zm.group(2).strip(), "fw":int(zm.group(3))})
    h["zauber"] = z
    return h

names = {15:"Geron Waisenmacher",16:"Layariel Wipfelglanz",17:"Arbosch Sohn des Angrax",
         18:"Mirhiban al’Orhima",19:"Carolan Calavanti",20:"Tjalva Garheltdottir"}
heroes = {}
for pg, nm in names.items():
    h = parse(doc[pg-1].get_text()); h["name"] = nm; heroes[nm] = h

open("dsa-pregens.js","w",encoding="utf-8").write("window.DSAPREGENS = "+json.dumps(heroes,ensure_ascii=False)+";\n")
# Verifikationsausgabe
for nm,h in heroes.items():
    print(f"\n### {nm} — {h['spezies']}/{h['kultur']}/{h['profession']} | EG würfe")
    print("  eig:", h["eig"], "| LeP",h["lep"],"AsP",h["asp"],"Schips",h["schips"])
    print("  Talente:",len(h["talente"]),"| Kampftechn.:",len(h["kampftechniken"]),"| Zauber:",len(h["zauber"]))
    print("  Beispiel-Talente:", dict(list(h["talente"].items())[:5]))
    print("  Schwerter/Bögen:", h["kampftechniken"].get("Schwerter"), h["kampftechniken"].get("Bögen"))
    if h["zauber"]: print("  Zauber:", h["zauber"])
