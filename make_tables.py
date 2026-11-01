import xml.etree.ElementTree as ET
from datetime import date
from collections import defaultdict

NS = "{http://www.tei-c.org/ns/1.0}"
LANDING = date(1908, 6, 18)
NAME_TAGS = {NS + t for t in ("placeName", "persName", "orgName", "term")}

def text_of(el):
    if el.tag in (NS + "expan", NS + "rt"):
        return ""
    parts = [el.text or ""]
    for ch in el:
        parts.append(text_of(ch))
        parts.append(ch.tail or "")
    return "".join(parts)

def load(path):
    body = ET.parse(path).getroot().find(f"{NS}text/{NS}body")
    when, entries = {}, []
    for div in body.iter(NS + "div"):
        if div.get("type") == "entry":
            d = date.fromisoformat(div.find(f"{NS}dateline/{NS}date").get("when"))
            entries.append((d, div))
            for el in div.iter():
                when[el] = d
    return body, when, entries

def name_forms(body, when):
    table = defaultdict(dict)
    for el in body.iter():
        if el.tag in NAME_TAGS and el.get("ref"):
            ref = el.get("ref").split("#")[-1]
            form = text_of(el).strip()
            count, first = table[ref].get(form, (0, None))
            d = when.get(el)
            if d and (first is None or d < first):
                first = d
            table[ref][form] = (count + 1, first)
    return table

def show_date(d):
    return d.isoformat() if d else "undated (cover/appendix)"

m_body, m_when, m_entries = load("mizuno.xml")
u_body, u_when, _ = load("uetsuka.xml")
M = name_forms(m_body, m_when)
U = name_forms(u_body, u_when)

print("TABLE 1. Mizuno: names written more than one way")
print("(form: occurrences, first dated attestation)")
for ref in ["pl_petropolis", "pl_dumont", "ps_monteiro", "ps_sobral", "ps_dumont_manager",
            "pl_estrangeiro", "pl_buenosaires", "lex_broker", "pl_grandhotel", "pl_capetown"]:
    print(f"\n{ref}")
    for form, (n, first) in sorted(M.get(ref, {}).items(), key=lambda kv: kv[1][1] or date.max):
        print(f"  {form}: {n}  first {show_date(first)}")

print("\n\nTABLE 2. Same place, two writers (occurrences)")
for ref in ["pl_brazil", "pl_singapore", "pl_rio", "pl_rio_state", "pl_dumont", "pl_reunion",
            "pl_capetown", "pl_saopaulo", "pl_capeofgoodhope", "pl_guatapara"]:
    m = ", ".join(f"{f} {n}" for f, (n, _) in M.get(ref, {}).items()) or "-"
    u = ", ".join(f"{f} {n}" for f, (n, _) in U.get(ref, {}).items()) or "-"
    print(f"\n{ref}\n  Mizuno:  {m}\n  Uetsuka: {u}")

print("\n\nTABLE 3. Mizuno: first attestations, counted from landing at Santos (1908-06-18)")
MARKERS = [("「リ」 in a verb (帰「リ」/下「リ」)", ["帰「リ」", "下「リ」"]),
           ("来聖", ["来聖"]), ("帰聖", ["帰聖"]), ("着聖", ["着聖"]),
           ("聖市", ["聖市"]), ("聖州", ["聖州"]), ("聖都", ["聖都"]),
           ("ミルレース", ["ミルレース"]), ("コントス / コント", ["コント"])]
for label, needles in MARKERS:
    hits = [d for d, div in m_entries if any(n in text_of(div) for n in needles)]
    if hits:
        first = min(hits)
        print(f"  {label}: first {first.isoformat()} ({(first - LANDING).days:+d} days), in {len(hits)} entries")
    else:
        print(f"  {label}: not found in dated entries")

print("\n\nTABLE 4. Group labels (categories of belonging)")
for name, body, when in (("Mizuno", m_body, m_when), ("Uetsuka", u_body, u_when)):
    cats = defaultdict(dict)
    for el in body.iter(NS + "rs"):
        if el.get("type") != "group":
            continue
        cat = (el.get("ana") or "").split("#")[-1]
        label = text_of(el).strip()
        n, first = cats[cat].get(label, (0, None))
        d = when.get(el)
        if d and (first is None or d < first):
            first = d
        cats[cat][label] = (n + 1, first)
    print(f"\n{name}")
    for cat in sorted(cats):
        print(f"  {cat} ({sum(v[0] for v in cats[cat].values())})")
        for label, (n, first) in cats[cat].items():
            print(f"    {label}: {n}" + (f", first {first.isoformat()}" if first else ""))

runs = [int(e.get("quantity")) for e in m_body.iter(NS + "measure") if e.get("type") == "dayRun"]
total = [e.get("quantity") for e in m_body.iter(NS + "measure") if e.get("type") == "total"]
pos = sum(1 for e in m_body.iter(NS + "seg") if e.get("type") == "noonPosition")
print("\n\nVOYAGE CHECK")
print(f"  Noon positions: {pos}")
print(f"  Daily runs recorded: {len(runs)}, adding up to {sum(runs)} miles")
print(f"  Mizuno's own stated total: {', '.join(total)} miles")
