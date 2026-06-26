# -*- coding: utf-8 -*-
"""dsa-lore.json -> dsa-lore.js (window.DSALORE) fuer den Bogen."""
import json, re
L = json.load(open("dsa-lore.json", encoding="utf-8"))
def norm(t):
    t = re.sub(r"(\w)\s+-(\w)", r"\1-\2", t)   # "Praios -Geweihte" -> "Praios-Geweihte" (Link-Artefakt)
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)      # Leerzeichen vor Satzzeichen
    return re.sub(r"\s{2,}", " ", t).strip()
for k in ("spezies", "kulturen", "professionen"):
    L.setdefault(k, {})
    for e in L[k].values():
        if e.get("text"): e["text"] = norm(e["text"])
with open("dsa-lore.js", "w", encoding="utf-8") as f:
    f.write("window.DSALORE = " + json.dumps(L, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("dsa-lore.js geschrieben:",
      {k: len(L[k]) for k in ("spezies", "kulturen", "professionen")})
