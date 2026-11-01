import re, html
from pathlib import Path

# Kanji numerals: 廿九=29, 卅一=31, 百三十二=132, positional 二三=23
D = dict(zip("〇一二三四五六七八九", range(10)))

def kanji_num(s):
    if len(s) > 1 and all(c in D for c in s):
        return int("".join(str(D[c]) for c in s))
    s = s.replace("廿", "二十").replace("卅", "三十")
    total = 0
    if "百" in s:
        h, _, s = s.partition("百"); total += (D[h] if h else 1) * 100
    if "十" in s:
        t, _, s = s.partition("十"); total += (D[t] if t else 1) * 10
    if s:
        total += D[s]
    return total

# A diary entry starts with a line like 四月廿九日　晴　水曜日
ENTRY = re.compile(r"^([一二三四五六七八九十]+)月([〇一二三四五六七八九十廿卅]+)日\s*(.*)$")

def build(raw, year=1908):
    out, open_div = [], False
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = ENTRY.match(line)
        if m:
            if open_div:
                out.append("</p></div>")
            mo, dy = kanji_num(m.group(1)), kanji_num(m.group(2))
            iso = f"{year}-{mo:02d}-{dy:02d}"
            out.append(f'<div type="entry" xml:id="e{iso}"><dateline>'
                       f'<date when="{iso}">{m.group(1)}月{m.group(2)}日</date> '
                       f'{html.escape(m.group(3))}</dateline><p>')
            open_div = True
        elif open_div:
            out.append(html.escape(line) + '<lb ed="ndl"/>')
    if open_div:
        out.append("</p></div>")
    return "\n".join(out)

TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="https://vault.tei-c.org/P5/current/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="ja">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>笠戸丸航海日記 (draft)</title></titleStmt>
      <publicationStmt><p>Working draft.</p></publicationStmt>
      <sourceDesc><p>NDL transcription, https://www.ndl.go.jp/brasil/text/t102.html</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text><body>
{body}
  </body></text>
</TEI>
"""

raw = Path("raw/mizuno_ndl_raw.txt").read_text(encoding="utf-8")
body = build(raw)
Path("mizuno_draft.xml").write_text(TEMPLATE.format(body=body), encoding="utf-8")
print("Entries written:", body.count('type="entry"'))