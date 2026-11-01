import re, html
import xml.etree.ElementTree as ET
from pathlib import Path

RAW = Path("raw/uetsuka_ndl_raw.txt")
OUT = Path("uetsuka.xml")
AUTH = Path("authority.xml")
A = "authority.xml#"

# ---------- 1. cut the two dispatches out of the page ----------
lines = [l.strip() for l in RAW.read_text(encoding="utf-8").splitlines()]
lines = [l for l in lines if l]

def find(pred, start, what):
    for k in range(start, len(lines)):
        if pred(lines[k]):
            return k
    raise SystemExit(f"Could not find {what} - nothing written.")

i_by1 = find(lambda l: "出張員法学士" in l, 0, "the first byline")
i_h1 = i_by1 - 1
if "喜望" not in lines[i_h1]:
    raise SystemExit("The line before the first byline is not the first heading - nothing written.")
i_h2 = find(lambda l: l.startswith("日本移民伯国に着す"), i_by1, "the second heading")
if '法学士' not in lines[i_h2 + 1] and '法学士' in lines[i_h2 + 2]:
    lines[i_h2] = lines[i_h2] + '　' + lines[i_h2 + 1]
    del lines[i_h2 + 1]
i_by2 = i_h2 + 1
if "法学士" not in lines[i_by2]:
    raise SystemExit("Could not find the second byline - nothing written.")
i_end = find(lambda l: "八月八日着" in l, i_h2, "the end of the second dispatch")

d1 = lines[i_by1 + 1:i_h2]
d2 = lines[i_by2 + 1:i_end + 1]
k = next((j for j, l in enumerate(d1) if l.startswith("▲")), None)
if k is None:
    raise SystemExit("Could not find the first ▲ subheading - nothing written.")
intro, letter1 = d1[:k], d1[k:]

CLOSE = re.compile(r"(（[^（）]*(?:笠戸丸|着)）)$")
def split_close(ls):
    m = CLOSE.search(ls[-1])
    if not m:
        raise SystemExit("Could not find a dispatch's closing date - nothing written.")
    rest = ls[-1][:m.start()]
    return (ls[:-1] + [rest] if rest else ls[:-1]), m.group(1)

letter1, close1 = split_close(letter1)
letter2, close2 = split_close(d2)
close1 = html.escape(close1).replace("六月四日", '<date when="1908-06-04">六月四日</date>', 1)
close2 = (html.escape(close2)
          .replace("七月二日", '<date type="sent" when="1908-07-02">七月二日</date>', 1)
          .replace("八月八日", '<date type="received" when="1908-08-08">八月八日</date>', 1))

# ---------- 2. inline: ruby glosses and the Portuguese cheer ----------
RUBY = [("船暈", "ふなゑい"), ("竊", "ひそか"), ("活惚", "くわつぼれ"), ("鳩", "あつ"),
        ("曩", "さき"), ("快怡", "くわいゐ"), ("穏波洋々", "おんぱやうやう"),
        ("暫時", "しばらく"), ("麺麭", "ぱん"), ("欹", "そばた"), ("喜悦", "よろこび")]
CHEER = "ビーブア、ド、ブラジル"
stats = {"subsections": 0, "ruby": 0, "foreign": 0}

def enc(s):
    s = html.escape(s, quote=False)
    for base, rd in RUBY:
        new = f"<ruby><rb>{base}</rb><rt>{rd}</rt></ruby>"
        for old in (f"{base}({rd})", f"{base}（{rd}）", f"{base}{rd}"):
            if old in s:
                stats["ruby"] += s.count(old)
                s = s.replace(old, new)
    if CHEER in s:
        stats["foreign"] += s.count(CHEER)
        s = s.replace(CHEER, f'<foreign xml:lang="pt-Kana">{CHEER}</foreign>')
    return s

def letter(ls, closing):
    out, is_open = [], False
    for l in ls:
        if l.startswith("▲"):
            if is_open:
                out.append("</div>")
            out.append(f'<div type="subsection"><head>{enc(l)}</head>')
            is_open = True
            stats["subsections"] += 1
        else:
            if not is_open:
                out.append('<div type="subsection">')
                is_open = True
            out.append(f"<p>{enc(l)}</p>")
    if is_open:
        out.append("</div>")
    out.append(f"<closer><dateline>{closing}</dateline></closer>")
    return "\n".join(out)

intro_xml = "\n".join(f"<p>{enc(l)}</p>" for l in intro)
parts = [f'<div type="dispatch" n="1" xml:id="d1">\n<head>{enc(lines[i_h1])}</head>',
         f"<byline>{enc(lines[i_by1])}</byline>"]
if intro:
    parts.append(f'<div type="editorial">\n{intro_xml}\n</div>')
parts += [f'<div type="letter">\n{letter(letter1, close1)}\n</div>', "</div>",
          f'<div type="dispatch" n="2" xml:id="d2">\n<head>{enc(lines[i_h2])}</head>',
          f"<byline>{enc(lines[i_by2])}</byline>",
          f'<div type="letter">\n{letter(letter2, close2)}\n</div>', "</div>"]
body = "<text><body>\n" + "\n".join(parts) + "\n</body></text>"

# ---------- 3. groups and names ----------
GROUPS = {
    "沖縄県人": ("grp_okinawa", "cat_prefecture"), "沖縄移民": ("grp_okinawa", "cat_prefecture"),
    "鹿児島県移民": ("grp_kagoshima", "cat_prefecture"), "鹿児島移民": ("grp_kagoshima", "cat_prefecture"),
    "愛媛高知県人": ("grp_ehime_kochi", "cat_prefecture"), "高知愛媛県人": ("grp_ehime_kochi", "cat_prefecture"),
    "愛媛県人": ("grp_ehime", "cat_prefecture"),
    "日本移民": ("grp_japanese", "cat_nation"), "日本人": ("grp_japanese_people", "cat_nation"),
    "伊太利移民": ("grp_italians", "cat_nation"), "伯国人": ("grp_brazilians", "cat_nation"),
    "火夫": ("grp_stokers", "cat_labour"),
}
GROUP_RX = re.compile("|".join([re.escape(g) for g in sorted(GROUPS, key=len, reverse=True)]
                               + [r"(?P<ware>我移民(?!船))"]))

def wrap_group(m):
    t = m.group(0)
    ref, cat = ("grp_japanese", "cat_nation") if m.lastgroup == "ware" else GROUPS[t]
    return f'<rs type="group" ref="{A}{ref}" ana="{A}{cat}">{t}</rs>'

LIT = {}
for f, r in {"神戸": "pl_kobe", "新嘉坡": "pl_singapore", "喜望峯": "pl_capeofgoodhope",
             "喜望峰": "pl_capeofgoodhope", "スマトラ": "pl_sumatra", "印度洋": "pl_indianocean",
             "レニオン": "pl_reunion", "亜弗利加": "pl_africa", "ケープ・タウン": "pl_capetown",
             "香港": "pl_hongkong", "サントス": "pl_santos", "伯国": "pl_brazil",
             "伯剌西爾": "pl_brazil", "ブラジル": "pl_brazil", "サンパウロ": "pl_saopaulo",
             "カナン": "pl_canaa", "イツー": "pl_itu", "グワタパラ": "pl_guatapara",
             "カタバラ": "pl_guatapara", "サンマルチニヤ": "pl_saomartinho", "ヂユモント": "pl_dumont",
             "リオ州": "pl_rio_state", "秘露": "pl_peru", "ブラス": "pl_bras", "東京": "pl_tokyo"}.items():
    LIT[f] = ("placeName", r)
for f, r in {"上塚周平": "ps_uetsuka", "上塚": "ps_uetsuka", "水野龍": "ps_mizuno", "水野": "ps_mizuno",
             "江藤哲蔵": "ps_eto", "朝日胤一": "ps_asahi", "三浦荒次郎": "ps_miura", "三浦": "ps_miura",
             "鈴木貞次郎": "ps_suzuki_teijiro", "モンテイロ": "ps_monteiro"}.items():
    LIT[f] = ("persName", r)
for f, r in {"皇国殖民会社": "org_kokoku", "皇国移民会社": "org_kokoku", "東洋汽船会社": "org_toyo"}.items():
    LIT[f] = ("orgName", r)
for f, r in {"サルン": "lex_saloon", "カビン": "lex_cabin", "ステーシヨン": "lex_station",
             "インクライン": "lex_incline", "フオーク": "lex_fork", "ソープ": "lex_soup",
             "テーブル": "lex_table", "セメント": "lex_cement"}.items():
    LIT[f] = ("term", r)
NAME_RX = re.compile("|".join(re.escape(f) for f in sorted(LIT, key=len, reverse=True)))

def wrap_name(m):
    elem, ref = LIT[m.group(0)]
    return f'<{elem} ref="{A}{ref}">{m.group(0)}</{elem}>'

TAG = re.compile(r"(<[^>]+>)")
SKIP = {"placeName", "persName", "orgName", "term", "rt", "foreign", "date"}

def walk(s, rx, repl):
    out, stack = [], []
    for tok in TAG.split(s):
        if tok.startswith("<"):
            out.append(tok)
            if tok.startswith("</"):
                if stack:
                    stack.pop()
            elif not tok.endswith("/>"):
                stack.append(re.match(r"<([\w:]+)", tok).group(1))
        elif tok:
            out.append(tok if SKIP.intersection(stack) else rx.sub(repl, tok))
    return "".join(out)

body = walk(body, GROUP_RX, wrap_group)
body = walk(body, NAME_RX, wrap_name)

# ---------- 4. header and output ----------
HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="https://vault.tei-c.org/P5/current/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="ja">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>伯国移民船喜望峯に入る／日本移民伯国に着す</title>
        <title xml:lang="en" type="sub">Uetsuka Shūhei's two dispatches on the Kasato-maru voyage (1908): a TEI encoding</title>
        <author>上塚周平</author>
        <respStmt><resp>TEI encoding</resp><name>Andrew Lao</name></respStmt>
      </titleStmt>
      <publicationStmt>
        <p>Working file. Do not redistribute until the National Diet Library's reuse terms for its transcription have been confirmed.</p>
      </publicationStmt>
      <sourceDesc>
        <bibl type="transcription">
          <title>上塚周平からの航海の状況の速報</title>
          <publisher>国立国会図書館 (National Diet Library), ブラジル移民の100年</publisher>
          <date when="2009-03-04">2009</date>
          <ptr target="https://www.ndl.go.jp/brasil/text/t103.html"/>
          <note>Whole page copied on 2026-11-01; see raw/SOURCE.txt.</note>
        </bibl>
        <bibl type="original">
          <author>上塚周平</author>
          <title level="a">伯国移民船喜望峰に入る</title>
          <title level="a">日本移民伯国に着す</title>
          <title level="j">商工世界太平洋</title>
          <biblScope unit="volume">7</biblScope>
          <biblScope unit="issue">18</biblScope>
          <date when="1908-09-01">明治41年9月1日</date>
        </bibl>
      </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <editorialDecl>
        <p>The text follows the NDL transcription. It has not yet been collated with the magazine.</p>
        <p>div type="editorial" holds the magazine's introduction to the first dispatch; it is not Uetsuka's text.</p>
        <p>The ▲ subheadings are kept as printed. Whether they were written by Uetsuka or by the magazine's editors is unknown.</p>
        <p>Readings that the NDL shows after certain words are encoded as ruby. ビーブア、ド、ブラジル is encoded as foreign with xml:lang="pt-Kana" (Portuguese speech written in katakana).</p>
        <p>The NDL's citation gives 喜望峰 in the first title, while its heading reads 喜望峯; both are kept as found.</p>
        <p>Places, persons, organisations, contact terms and group labels point to authority.xml and are tagged throughout, including subheadings.</p>
      </editorialDecl>
    </encodingDesc>
    <revisionDesc>
      <change when="2026-11-01">Generated with build_uetsuka.py from raw/uetsuka_ndl_raw.txt; automatic markup not yet fully reviewed by hand.</change>
    </revisionDesc>
  </teiHeader>
"""
out = HEADER + body + "\n</TEI>\n"
OUT.write_text(out, encoding="utf-8")

# ---------- 5. add Uetsuka's new names to authority.xml ----------
NEW_PLACES = """
      <place xml:id="pl_kobe"><placeName type="reg" xml:lang="ja">神戸</placeName></place>
      <place xml:id="pl_capeofgoodhope"><placeName type="reg" xml:lang="en">Cape of Good Hope</placeName><placeName type="attested">喜望峯</placeName><placeName type="attested">喜望峰</placeName></place>
      <place xml:id="pl_sumatra"><placeName type="reg" xml:lang="en">Sumatra</placeName><placeName type="attested">スマトラ</placeName></place>
      <place xml:id="pl_indianocean"><placeName type="reg" xml:lang="en">Indian Ocean</placeName><placeName type="attested">印度洋</placeName></place>
      <place xml:id="pl_hongkong"><placeName type="reg" xml:lang="en">Hong Kong</placeName><placeName type="attested">香港</placeName></place>
      <place xml:id="pl_peru"><placeName type="reg" xml:lang="es">Perú</placeName><placeName type="attested">秘露</placeName></place>
      <place xml:id="pl_guatapara"><placeName type="reg" xml:lang="pt" cert="medium">Fazenda Guatapará</placeName><placeName type="attested">グワタパラ</placeName><placeName type="attested">カタバラ</placeName><note>Uetsuka uses both forms in his second dispatch.</note></place>
      <place xml:id="pl_saomartinho"><placeName type="reg" xml:lang="pt" cert="medium">Fazenda São Martinho</placeName><placeName type="attested">サンマルチニヤ</placeName></place>
      <place xml:id="pl_bras"><placeName type="reg" xml:lang="pt">Brás (São Paulo)</placeName><placeName type="attested">ブラス</placeName></place>"""
NEW_PERSONS = """
      <person xml:id="ps_mizuno"><persName type="reg" xml:lang="ja">水野龍</persName><persName type="attested">水野</persName><note>President (社長) of the Kōkoku Shokumin Kaisha; author of the voyage diary.</note></person>
      <person xml:id="ps_eto"><persName type="reg" xml:lang="ja">江藤哲蔵</persName><note>Member of the Diet (代議士) who recommended Uetsuka, per the magazine's introduction.</note></person>
      <person xml:id="ps_asahi"><persName type="reg" xml:lang="ja">朝日胤一</persName><note>Law graduate posted to Peru, per the magazine's introduction.</note></person>
      <person xml:id="ps_suzuki_teijiro"><persName type="reg" xml:lang="ja">鈴木貞次郎</persName><note>At the São Paulo immigrant hostel, per Uetsuka's second dispatch.</note></person>"""
NEW_ORGS = """
      <org xml:id="org_kokoku"><orgName xml:lang="ja">皇国殖民会社</orgName><orgName type="attested">皇国移民会社</orgName><note>皇国移民会社 appears once, in the magazine's introduction.</note></org>"""
NEW_GROUPS = """
      <personGrp xml:id="grp_kagoshima"><p>鹿児島(県)移民: emigrants from Kagoshima.</p></personGrp>
      <personGrp xml:id="grp_ehime"><p>愛媛県人: people from Ehime.</p></personGrp>
      <personGrp xml:id="grp_ehime_kochi"><p>愛媛高知県人, 高知愛媛県人: people from Ehime and Kōchi.</p></personGrp>
      <personGrp xml:id="grp_japanese_people"><p>日本人: the Japanese.</p></personGrp>
      <personGrp xml:id="grp_italians"><p>伊太利移民: Italian immigrants.</p></personGrp>
      <personGrp xml:id="grp_brazilians"><p>伯国人: Brazilians.</p></personGrp>"""
NEW_LEX = """
      <item xml:id="lex_saloon"><term xml:lang="en">saloon</term></item>
      <item xml:id="lex_cabin"><term xml:lang="en">cabin</term></item>
      <item xml:id="lex_station"><term xml:lang="en">station</term></item>
      <item xml:id="lex_incline"><term xml:lang="en">incline</term></item>
      <item xml:id="lex_fork"><term xml:lang="en">fork</term></item>
      <item xml:id="lex_soup"><term xml:lang="en">soup</term></item>
      <item xml:id="lex_table"><term xml:lang="en">table</term></item>
      <item xml:id="lex_cement"><term xml:lang="en">cement</term></item>"""

auth = AUTH.read_text(encoding="utf-8")
if 'xml:id="pl_kobe"' not in auth:
    auth = auth.replace("</listPlace>", NEW_PLACES + "\n    </listPlace>", 1)
    k = auth.find("</listPerson>")
    auth = auth[:k] + NEW_PERSONS.lstrip("\n") + "\n    " + auth[k:]
    auth = auth.replace("</listOrg>", NEW_ORGS + "\n    </listOrg>", 1)
    k = auth.rfind("</listPerson>")
    auth = auth[:k] + NEW_GROUPS.lstrip("\n") + "\n    " + auth[k:]
    auth = auth.replace("</list>", NEW_LEX + "\n    </list>", 1)
    AUTH.write_text(auth, encoding="utf-8")
    print("authority.xml: new records added.")
else:
    print("authority.xml: new records already present.")

# ---------- 6. checks and report ----------
def norm(s):
    return re.sub(r"[\s()（）]", "", s)

def wf(text):
    try:
        ET.fromstring(text.encode("utf-8"))
        return "yes"
    except ET.ParseError as err:
        return f"NO - {err}"

body_text = norm(html.unescape(re.sub(r"<[^>]+>", "", body)))
raw_text = norm("".join(lines[i_h1:i_end + 1]))
print("Dispatches: 2 | subsections:", stats["subsections"])
print("Ruby glosses:", stats["ruby"], "| Portuguese cheer marked:", stats["foreign"])
for el in ("placeName", "persName", "orgName", "term"):
    print(f"{el}:", len(re.findall(rf"<{el} ref=", body)))
print("group labels (rs):", body.count('<rs type="group"'))
print("Well-formed uetsuka.xml:", wf(out))
print("Well-formed authority.xml:", wf(AUTH.read_text(encoding="utf-8")))
print("Text check:", "OK - no characters added or lost" if body_text == raw_text else "MISMATCH - tell Claude")

print("\nPlace forms in Uetsuka:")
forms = {}
for ref, t in re.findall(r'<placeName ref="authority\.xml#(\w+)">(.*?)</placeName>', body):
    forms.setdefault(ref, {}).setdefault(t, 0)
    forms[ref][t] += 1
for ref in sorted(forms):
    print(" ", ref, forms[ref])
