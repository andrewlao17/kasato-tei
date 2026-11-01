import re
from pathlib import Path

p = Path("mizuno.xml")
x = p.read_text(encoding="utf-8")
if "<editorialDecl>" in x:
    raise SystemExit("The new header is already in place - nothing changed.")

NEW = """<teiHeader>
    <fileDesc>
      <titleStmt>
        <title>笠戸丸航海日記</title>
        <title xml:lang="en" type="sub">Mizuno Ryō, Kasato-maru kōkai nikki (1908): a TEI encoding</title>
        <author>水野龍</author>
        <respStmt><resp>TEI encoding</resp><name>[Your name]</name></respStmt>
      </titleStmt>
      <publicationStmt>
        <p>Working file. Do not redistribute until the National Diet Library's reuse terms for its transcription have been confirmed.</p>
      </publicationStmt>
      <sourceDesc>
        <bibl type="transcription">
          <title>水野龍「笠戸丸航海日記」</title>
          <publisher>国立国会図書館 (National Diet Library), ブラジル移民の100年</publisher>
          <date when="2009-03-04">2009</date>
          <ptr target="https://www.ndl.go.jp/brasil/text/t102.html"/>
          <note>Text copied from this page on 2026-11-01; see raw/SOURCE.txt. Parentheses around the NDL's small annotations (ママ, ブラジル) were lost in copying.</note>
        </bibl>
        <msDesc>
          <msIdentifier>
            <settlement>Bastos</settlement>
            <repository>山中三郎記念バストス地域史料館 (Museu Histórico Regional Saburo Yamanaka de Bastos)</repository>
            <msName>笠戸丸航海日記</msName>
          </msIdentifier>
          <msContents><summary>Diary, 29 April to 3 September 1908, with undated notes inside the cover.</summary></msContents>
        </msDesc>
      </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <editorialDecl>
        <p>The text follows the NDL transcription. It has not yet been collated with the NDL's photographs of the manuscript.</p>
        <p>lb with ed="ndl" marks the NDL's line breaks, not the manuscript's. Headings with type="editorial" are the NDL's, not Mizuno's.</p>
        <p>The NDL's (ママ) markers are encoded as sic and the marker itself is omitted; the extent of each sic is the encoder's judgement. The NDL's square brackets are encoded as supplied, and its □ (illegible character) as gap. The gloss ブラジル on 舞楽而留 is encoded as ruby with cert="medium", because the copied text cannot show whether the gloss is the author's.</p>
        <p>「リ」 is encoded as an abbreviation of リヨ (Rio de Janeiro). 聖 standing for São Paulo is encoded as placeName with type="sinoAbbrev".</p>
        <p>The line 前日午後六時, which precedes the first dated entry, is kept at the end of the cover notes; its relation to the entry of 29 April is uncertain.</p>
        <p>seg type="weather" and seg type="noonPosition" mark weather words and the ship's noon positions. measure with unit="mile" records 哩 as written, and its type distinguishes dayRun, remaining, total and other. Currency amounts are given in mil-réis (1 conto = 1,000 mil-réis) or yen.</p>
        <p>Places, persons, organisations, contact terms and group labels point to authority.xml. Personal names are tagged only in the dated entries. Identifications marked with cert are the encoder's proposals. Names whose referent the diary leaves unclear (for example 鈴木, 安田, 大野, 古谷) are not yet tagged.</p>
      </editorialDecl>
    </encodingDesc>
    <revisionDesc>
      <change when="2026-11-01">Structure generated with make_skeleton.py and add_sections.py; the entry of 29 April encoded by hand.</change>
      <change when="2026-11-01">Weather, positions, distances and currency added with encode_voyage.py and encode_shore.py.</change>
      <change when="2026-11-01">Editorial signs encoded with encode_editorial.py; names, terms and group labels with encode_names.py. Automatic markup not yet fully reviewed by hand.</change>
    </revisionDesc>
  </teiHeader>"""

x, n = re.subn(r"<teiHeader>.*?</teiHeader>", lambda m: NEW, x, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Could not find the teiHeader - nothing changed.")
x = x.replace("<head>表紙裏</head>", '<head type="editorial">表紙裏</head>')
p.write_text(x, encoding="utf-8")
print("Header replaced.")
