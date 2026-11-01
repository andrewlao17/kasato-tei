import re
from pathlib import Path

p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")
if "<sic>" in x:
    raise SystemExit("Editorial markup is already in the file - nothing changed.")

i = x.find("<text>")
head, body = x[:i], x[i:]

counts = {}
FIXES = [
    ("六十九ママ分", "<sic>六十九</sic>分", "sic"),
    ("サンプママランシスコ", "<sic>サンプ</sic>ランシスコ", "sic"),
    ("公正ママ役場", "<sic>公正</sic>役場", "sic"),
    ("供ママにして", "<sic>供</sic>にして", "sic"),
    ("舞楽而留ブラジル", '<ruby cert="medium"><rb>舞楽而留</rb><rt>ブラジル</rt></ruby>', "ruby"),
    ("「リ」", "「<choice><abbr>リ</abbr><expan>リヨ</expan></choice>」", "abbr"),
    ("Turn Abont", '<foreign xml:lang="en">Turn <sic>Abont</sic></foreign>', "foreign"),
]
for old, new, kind in FIXES:
    counts[kind] = counts.get(kind, 0) + body.count(old)
    body = body.replace(old, new)

body, counts["supplied"] = re.subn(r"\[([^\]]+)\]", r"<supplied>\1</supplied>", body)
body, counts["gap"] = re.subn(
    r"□+", lambda m: f'<gap reason="illegible" unit="chars" quantity="{len(m.group(0))}"/>', body)

p.write_text(head + body, encoding="utf-8")
print("Changes:", counts)
print("ママ markers left:", body.count("ママ"))
