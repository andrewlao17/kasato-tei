import re
from pathlib import Path

A = "authority.xml#"
p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")
if A in x:
    raise SystemExit("Names are already tagged in the file - nothing changed.")
i = x.find("<text>")
head, body = x[:i], x[i:]

# --- 1. spots prepared in the editorial stage ---
SPOTS = [
    ("「<choice><abbr>リ</abbr><expan>リヨ</expan></choice>」",
     f'「<placeName ref="{A}pl_rio" type="abbrev"><choice><abbr>リ</abbr><expan>リヨ</expan></choice></placeName>」'),
    ("<rb>舞楽而留</rb>", f'<rb><placeName ref="{A}pl_brazil">舞楽而留</placeName></rb>'),
    ("<sic>サンプ</sic>ランシスコ", f'<placeName ref="{A}pl_sanfrancisco"><sic>サンプ</sic>ランシスコ</placeName>'),
]
for old, new in SPOTS:
    body = body.replace(old, new)

# --- 2. word lists (every ref here exists in authority.xml) ---
PLACES = {
    "ペツロホリス": "pl_petropolis", "ペツロポリス": "pl_petropolis", "ペトロポリス": "pl_petropolis",
    "Petropolis": "pl_petropolis", "ヅーモント": "pl_dumont", "ヅーモン": "pl_dumont",
    "リヨ州": "pl_rio_state", "リヨ": "pl_rio", "サンパウロ": "pl_saopaulo", "聖嘉坡": "pl_singapore",
    "ケープタウン": "pl_capetown", "Cape Town": "pl_capetown", "サントス": "pl_santos",
    "ニテロイ": "pl_niteroi", "マウリタス嶋": "pl_mauritius", "セントレウニオン嶋": "pl_reunion",
    "マダカスカル嶋": "pl_madagascar", "亜弗利加": "pl_africa", "舞楽而留": "pl_brazil",
    "ブラジル": "pl_brazil", "ブェノスアイレス": "pl_buenosaires", "ベノスアイルス": "pl_buenosaires",
    "カナン": "pl_canaa", "イツー": "pl_itu", "プライニヤ": "pl_prainha", "マカエ": "pl_macae",
    "スワ嶋": "pl_suwanose", "臥蛇嶋": "pl_gaja", "兄弟嶋": "pl_kyodai", "ラバ嶋": "pl_raba",
    "東京": "pl_tokyo", "岡山": "pl_okayama", "広嶋": "pl_hiroshima", "ニューカレドニヤ": "pl_newcaledonia",
    "ノルテ": "pl_estacao_norte", "セントラル": "pl_central", "ボハケデサウデ": "pl_bosque_saude",
    "クランドホテル": "pl_grandhotel", "グランドホテル": "pl_grandhotel", "ホテルアベニダ": "pl_hotel_avenida",
    "ストランヂェイロホテル": "pl_estrangeiro", "エストランヂェイロ": "pl_estrangeiro",
    "エストランヂェル": "pl_estrangeiro",
}
LATIN_LANG = {"Cape Town": "en", "Petropolis": "pt"}
ORGS = {"東洋汽船": "org_toyo", "三井物産会社": "org_mitsui", "コメルシヨ": "org_commercio",
        "ブラジル鉄道会社": "org_brazil_railway", "日伯商店": "org_nippaku",
        "藤崎商店": "org_fujisaki", "安田商店": "org_yasuda"}
TERMS = {"ミルレース": "lex_milreis", "コントス": "lex_conto", "コント": "lex_conto",
         "ブローカー": "lex_broker", "ブロカー": "lex_broker", "コンミッチー": "lex_committee",
         "アゼンシヤ": "lex_agencia", "パーサー": "lex_purser", "プログラム": "lex_programa",
         "フワンシーボル": "lex_fancyball"}
PERSONS = {
    "上塚": "ps_uetsuka", "三浦": "ps_miura", "神谷忠雄": "ps_kamiya", "神谷": "ps_kamiya",
    "三原": "ps_mihara", "田中": "ps_tanaka", "宮崎信造": "ps_miyazaki", "宮崎": "ps_miyazaki",
    "片岡": "ps_kataoka", "有川": "ps_arikawa", "加藤": "ps_kato", "後藤": "ps_goto",
    "馬場": "ps_baba", "成川": "ps_narikawa", "九玉": "ps_kudama", "伊丹": "ps_itami",
    "香山": "ps_koyama", "山形勇三郎": "ps_yamagata", "山形": "ps_yamagata",
    "水嶋唱一郎": "ps_mizushima", "水嶋": "ps_mizushima", "古川大斧": "ps_furukawa", "古川": "ps_furukawa",
    "モンテイロ": "ps_monteiro", "モンデイロ": "ps_monteiro", "ソブラー": "ps_sobral",
    "ソブラ": "ps_sobral", "ゾフラー": "ps_sobral", "デヒー": "ps_dumont_manager",
    "デビー": "ps_dumont_manager", "ダリーノ": "ps_darino", "ベント、ブエノ": "ps_bento_bueno",
    "ボッテリヨ": "ps_botteriyo", "ミカエル": "ps_michael",
}
LOW_CERT = {"香山"}
GROUPS = {
    "ヅーモン帰来移民": ("grp_dumont_returnees", "cat_status"),
    "耕地鉄道志望者": ("grp_choosers", "cat_labour"),
    "船員の逃走者": ("grp_crew_deserters", "cat_status"),
    "船員逃走者": ("grp_crew_deserters", "cat_status"),
    "沖縄移民": ("grp_okinawa", "cat_prefecture"),
    "熊本移民": ("grp_kumamoto", "cat_prefecture"),
    "日本移民": ("grp_japanese", "cat_nation"),
    "逃亡移民": ("grp_absconders", "cat_status"),
    "鉄道工夫": ("grp_railway", "cat_labour"),
    "鉄道人夫": ("grp_railway", "cat_labour"),
    "耕夫": ("grp_farmhands", "cat_labour"),
    "火夫": ("grp_stokers", "cat_labour"),
}

LIT_PLACES = {}
for f, r in PLACES.items():
    LIT_PLACES[f] = ("placeName", r, f' xml:lang="{LATIN_LANG[f]}"' if f in LATIN_LANG else "")
for f, r in ORGS.items():
    LIT_PLACES[f] = ("orgName", r, "")
for f, r in TERMS.items():
    LIT_PLACES[f] = ("term", r, "")
LIT_ALL = dict(LIT_PLACES)
for f, r in PERSONS.items():
    LIT_ALL[f] = ("persName", r, ' cert="low"' if f in LOW_CERT else "")

SPECIAL_SEI = r"(?P<sei>(?<=[来帰着])聖|聖(?=[市州都]))"
SPECIAL_PERSONS = [r"(?P<mon>(?<!ー)モン(?=氏|、))",
                   r"(?P<uchida_min>内田(?=公使))",
                   r"(?P<uchida_ship>内田(?=管船|氏))"]

def build_rx(lit, specials):
    alts = [re.escape(f) for f in sorted(lit, key=len, reverse=True)] + specials
    return re.compile("|".join(alts))

def make_repl(lit):
    def repl(m):
        t, g = m.group(0), m.lastgroup
        if g == "sei":
            return f'<placeName ref="{A}pl_saopaulo" type="sinoAbbrev">{t}</placeName>'
        if g == "mon":
            return f'<persName ref="{A}ps_monteiro" type="clipped">{t}</persName>'
        if g == "uchida_min":
            return f'<persName ref="{A}ps_uchida_minister">{t}</persName>'
        if g == "uchida_ship":
            return f'<persName ref="{A}ps_uchida_shipping">{t}</persName>'
        elem, ref, extra = lit[t]
        return f'<{elem} ref="{A}{ref}"{extra}>{t}</{elem}>'
    return repl

RX_PLACES, REPL_PLACES = build_rx(LIT_PLACES, [SPECIAL_SEI]), make_repl(LIT_PLACES)
RX_ALL, REPL_ALL = build_rx(LIT_ALL, [SPECIAL_SEI] + SPECIAL_PERSONS), make_repl(LIT_ALL)
GROUP_RX = re.compile("|".join(map(re.escape, sorted(GROUPS, key=len, reverse=True))))

def wrap_group(m):
    ref, cat = GROUPS[m.group(0)]
    return f'<rs type="group" ref="{A}{ref}" ana="{A}{cat}">{m.group(0)}</rs>'

# --- 3. walk the text, touching only text outside tags ---
TAG = re.compile(r"(<[^>]+>)")
SKIP = {"head", "placeName", "persName", "orgName", "term", "rt", "abbr", "expan", "sic", "foreign", "date"}

def walk(s, fn):
    out, stack = [], []
    for tok in TAG.split(s):
        if tok.startswith("<"):
            out.append(tok)
            if tok.startswith("</"):
                if stack:
                    stack.pop()
            elif not tok.endswith("/>"):
                stack.append(tok)
        elif tok:
            names = {re.match(r"<([\w:]+)", t).group(1) for t in stack}
            in_entry = any(t.startswith('<div type="entry"') for t in stack)
            out.append(fn(tok, names, in_entry))
    return "".join(out)

def groups_pass(text, names, in_entry):
    if not in_entry or names & SKIP:
        return text
    return GROUP_RX.sub(wrap_group, text)

def names_pass(text, names, in_entry):
    if names & SKIP:
        return text
    rx, repl = (RX_ALL, REPL_ALL) if in_entry else (RX_PLACES, REPL_PLACES)
    return rx.sub(repl, text)

body = walk(body, groups_pass)
body = walk(body, names_pass)
p.write_text(head + body, encoding="utf-8")

# --- 4. report ---
for el in ("placeName", "persName", "orgName", "term"):
    print(f"{el}:", len(re.findall(rf'<{el} ref="{re.escape(A)}', body)))
print("group labels (rs):", body.count('<rs type="group"'))

print("\nSpelling variants (referents written more than one way):")
TAGGED = re.compile(r'<(placeName|persName|orgName|term) ref="authority\.xml#(\w+)"[^>]*>(.*?)</\1>', re.S)
forms = {}
for el, ref, inner in TAGGED.findall(body):
    inner = re.sub(r"<expan>.*?</expan>", "", inner)
    surface = re.sub(r"<[^>]+>", "", inner)
    forms.setdefault(ref, {}).setdefault(surface, 0)
    forms[ref][surface] += 1
for ref in sorted(forms):
    if len(forms[ref]) > 1:
        print(" ", ref, forms[ref])
        