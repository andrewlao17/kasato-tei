from pathlib import Path

p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")

if 'xml:id="voyage"' in x:
    raise SystemExit("Sections are already in the file - nothing changed.")

SECTIONS = [
    ("e1908-04-29", '<div type="section" n="2" xml:id="voyage"><head type="editorial">笠戸丸航海 4月29日〜6月18日</head>\n'),
    ("e1908-06-19", '</div><div type="section" n="3" xml:id="hostel"><head type="editorial">移民収容所 6月19日〜7月3日</head>\n'),
    ("e1908-07-04", '</div><div type="section" n="4" xml:id="rio"><head type="editorial">リオ・デジャネイロ 7月4日〜8月7日</head>\n'),
    ("e1908-08-08", '</div><div type="section" n="5" xml:id="dumont"><head type="editorial">ドゥモント耕地の紛擾 8月8日〜9月3日</head>\n'),
]

for entry_id, snippet in SECTIONS:
    tag = f'<div type="entry" xml:id="{entry_id}"'
    if x.count(tag) != 1:
        raise SystemExit(f"Could not find the entry {entry_id} exactly once - nothing changed.")
    x = x.replace(tag, snippet + tag)

tag = '<div type="appendix"'
if x.count(tag) != 1:
    raise SystemExit("Could not find the appendix - nothing changed.")
x = x.replace(tag, "</div>\n" + tag)

p.write_text(x, encoding="utf-8")
print("Sections added.")