"""Fill the ICNGC (IEEE, OOXML Strict) Word template with 논문_KR_v2.md."""
import re, struct, sys, shutil, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_scan import top_items

ROOT = "/Users/jaehyeon/Documents/Obsidian Vault/2026/04.호서대학교/11.차세대컴퓨팅학회논문"
MD = f"{ROOT}/논문_KR_v2.md"
FIGS = {"Fig1.png": f"{ROOT}/JavaStream_키편향/figures/paper/Fig1.png",
        "Fig2.png": f"{ROOT}/JavaStream_키편향/figures/paper/Fig2.png"}
U = sys.argv[1]                      # unpacked template directory
KO = '<w:rFonts w:eastAsia="바탕" w:hint="eastAsia"/>'
CODE = '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:eastAsia="바탕" w:cs="Courier New"/>'
LANG = '<w:lang w:eastAsia="ko-KR"/>'
EMU = 914400

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def run(text, bold=False, ital=False, code=False, size=None, extra=""):
    rpr = (CODE if code else KO) + ("<w:b/>" if bold else "") + ("<w:i/><w:iCs/>" if ital else "") + extra
    if size:
        rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    rpr += LANG
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

LINK_DROP = {"공개 원문", "원문", "저자 교정본"}
TOKEN = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")

def inline(text, size=None, bold_all=False):
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("`"):
            out.append(run(part[1:-1], code=True, size=size or 18, bold=bold_all))
        elif part.startswith("**"):
            out.append(run(part[2:-2], bold=True, size=size))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(run(part[1:-1], ital=True, size=size, bold=bold_all))
        elif part.startswith("[") and "](" in part:
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part).groups()
            out.append(run(label, size=size, bold=bold_all))
        else:
            out.append(run(part, size=size, bold=bold_all))
    return "".join(out)

def para(style, body, ppr_extra=""):
    st = f'<w:pStyle w:val="{style}"/>' if style else ""
    return f"<w:p><w:pPr>{st}{ppr_extra}</w:pPr>{body}</w:p>"

def clean_ref(t):
    # doi: [10.x](url) -> doi: 10.x ; alternate-copy links dropped ; other links -> Available: url
    t = re.sub(r"doi: \[([^\]]+)\]\([^)]+\)", r"doi: \1", t)
    def repl(m):
        label, url = m.group(1), m.group(2)
        return "" if label in LINK_DROP else f"[Online]. Available: {url}"
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, t)
    t = re.sub(r"\s*세부 분기는.*?대조하였다\.", "", t)     # Korean working note in [9]
    t = t.replace("[Online]. Available: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html, [Online]. Available: ",
                  "[Online]. Available: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html, ")
    t = re.sub(r"\.\s*\.", ".", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])

IMG_IDS = {}
def image_para(name, width_in):
    w, h = png_size(FIGS[name])
    cx = int(width_in * EMU); cy = int(cx * h / w)
    rid = IMG_IDS[name]; pid = 101 + list(IMG_IDS).index(name)
    a = 'xmlns:a="http://purl.oclc.org/ooxml/drawingml/main"'
    pic = 'xmlns:pic="http://purl.oclc.org/ooxml/drawingml/picture"'
    drawing = (
        f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{pid}" name="{name}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks {a} noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic {a}><a:graphicData uri="http://purl.oclc.org/ooxml/drawingml/picture">'
        f'<pic:pic {pic}><pic:nvPicPr><pic:cNvPr id="{pid}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        f'</wp:inline></w:drawing></w:r>')
    return para(None, drawing, '<w:keepNext/><w:spacing w:before="6pt" w:after="0pt"/><w:jc w:val="center"/>')

BORDERS = ('<w:tblBorders><w:top w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
           '<w:start w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
           '<w:bottom w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
           '<w:end w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
           '<w:insideH w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
           '<w:insideV w:val="single" w:sz="2" w:space="0" w:color="auto"/></w:tblBorders>')

def table(rows, widths_pt):
    total = sum(widths_pt)
    grid = "".join(f'<w:gridCol w:w="{int(w * 20)}"/>' for w in widths_pt)
    trs = []
    for r, cells in enumerate(rows):
        header = r == 0
        tcs = []; c = 0; idx = 0
        while idx < len(cells):
            span = 1
            while idx + span < len(cells) and cells[idx + span] == "" and idx + span == len(cells) - 1 and not header:
                span += 1
            w = sum(widths_pt[c:c + span])
            gs = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
            style = "tablecolhead" if header else "tablecopy"
            keep = '<w:keepNext/>' if r < len(rows) - 1 else ''      # keep the whole table together
            jc = keep + ('<w:jc w:val="center"/>' if header else '<w:jc w:val="start"/>')
            text = cells[idx].replace(" ± ", "±")
            body = inline(text, size=15, bold_all=header) if text else ""
            tcs.append(f'<w:tc><w:tcPr><w:tcW w:w="{w:g}pt" w:type="dxa"/>{gs}<w:vAlign w:val="center"/></w:tcPr>'
                       f'{para(style, body, jc)}</w:tc>')
            c += span; idx += span
        trpr = '<w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if header else '') + '<w:jc w:val="center"/></w:trPr>'
        trs.append(f"<w:tr>{trpr}{''.join(tcs)}</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{total:g}pt" w:type="dxa"/><w:jc w:val="center"/>{BORDERS}'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:start w:w="2.5pt" w:type="dxa"/><w:end w:w="2.5pt" w:type="dxa"/></w:tblCellMar><w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')

def md_table(lines):
    rows = []
    for l in lines:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows

# ------------------------------------------------------------------ parse markdown
md = open(MD, encoding="utf-8").read()
md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
lines = md.split("\n")
title = next(l[2:].strip() for l in lines if l.startswith("# "))
abstract = keywords = None
content = []          # generated body XML pieces
refs = []
WIDE_SECT = TWO_COL_SECT = None   # filled from template

i = 0; section = None; pending_table_caption = None
TABLE_WIDTHS = {"I": [46, 94, 100], "II": [64, 28, 52, 48, 48], "III": [88, 72, 72, 100, 168]}
WIDE_TABLES = {"III"}; WIDE_FIGS = {"Fig1.png"}
while i < len(lines):
    l = lines[i].rstrip()
    if l.startswith("## "):
        section = l[3:].strip()
        if section == "초록":
            j = i + 1
            while not lines[j].strip(): j += 1
            abstract = lines[j].strip(); i = j + 1; continue
        if section == "참고문헌":
            content.append(("refhead", None))
        else:
            content.append(("h1", re.sub(r"^[IVX]+\.\s*", "", section)))
        i += 1; continue
    if l.startswith("### "):
        content.append(("h2", re.sub(r"^[A-Z]\.\s*", "", l[4:].strip()))); i += 1; continue
    if l.startswith("**색인어:**"):
        keywords = l.split("**색인어:**", 1)[1].strip(); i += 1; continue
    if section is None or not l.strip():
        i += 1; continue
    if section == "참고문헌":
        m = re.match(r"\[(\d+)\]\s+(.*)", l)
        if m: refs.append(clean_ref(m.group(2)))
        i += 1; continue
    m = re.match(r"!\[\[.*?/([^/\]]+)\]\]", l)
    if m:
        content.append(("fig", m.group(1))); i += 1; continue
    m = re.match(r"\*\*Fig\. (\d+)\.\*\*\s*(.*)", l)
    if m:
        content.append(("figcap", m.group(2))); i += 1; continue
    m = re.match(r"\*\*Table ([IVX]+)\.\s*(.*?)\*\*\s*$", l)
    if m:
        num, cap = m.group(1), m.group(2).rstrip(".")
        j = i + 1
        while not lines[j].strip(): j += 1
        tl = []
        while j < len(lines) and lines[j].strip().startswith("|"):
            tl.append(lines[j]); j += 1
        content.append(("table", (num, cap, md_table(tl)))); i = j; continue
    content.append(("p", l.strip())); i += 1

# ------------------------------------------------------------------ assemble document
doc_path = f"{U}/word/document.xml"
x = open(doc_path, encoding="utf-8").read()
b = x.index("<w:body>") + len("<w:body>"); e = x.index("</w:body>")
items = top_items(x[b:e])
texts = [re.sub(r"<[^>]+>", "", s) for _, s in items]
assert texts[0].startswith("Paper Title") and texts[10].startswith("Abstract") and "<w:sectPr" in items[86][1]

def first_ppr(s):
    return re.search(r"<w:pPr>.*?</w:pPr>", s, flags=re.S).group(0)

# title
title_ppr = re.sub(r"<w:spacing[^>]*/>", "", first_ppr(items[0][1]))
KERN = '<w:kern w:val="48"/>'
p_title = "<w:p>" + title_ppr + run(title, extra=KERN) + "</w:p>"
# authors: two blocks in two columns
au_ppr = first_ppr(items[4][1])
def author(name):
    s = 18
    br = '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:br/></w:r>'
    return (run(name, size=s) + br + run("[학과]", ital=True, size=s) + br + run("호서대학교", ital=True, size=s)
            + br + run("[도시], 대한민국", size=s) + br + run("[이메일]", size=s))
colbr = '<w:r><w:br w:type="column"/></w:r>'
p_auth = f"<w:p>{au_ppr}{author('[저자 1]')}{colbr}{author('[저자 2]')}</w:p>"
sect_auth = items[8][1].replace('<w:cols w:num="3" w:space="36pt"/>', '<w:cols w:num="2" w:space="36pt"/>')
assert sect_auth != items[8][1]
# abstract and keywords
p_abs = para("Abstract", run("초록", ital=True) + run("—") + inline(abstract))
p_kw = para("Keywords", run("색인어—") + inline(keywords))

# section breaks for wide floats, based on the two-column body section (item 86)
body_sect = re.search(r"<w:sectPr\b.*?</w:sectPr>", items[86][1], flags=re.S).group(0)
body_sect = re.sub(r'\s+w:rsid\w*="[^"]*"', "", body_sect)
one_col_sect = re.sub(r'<w:cols [^>]*/>', '<w:cols w:space="18pt"/>', body_sect)
brk_two = f"<w:p><w:pPr><w:spacing w:before=\"0pt\" w:after=\"0pt\"/>{body_sect}</w:pPr></w:p>"
brk_one = f"<w:p><w:pPr><w:spacing w:before=\"0pt\" w:after=\"0pt\"/>{one_col_sect}</w:pPr></w:p>"

IMG_IDS.update({"Fig1.png": "rIdFig1", "Fig2.png": "rIdFig2"})
def is_wide(c):
    return (c[0] == "fig" and c[1] in WIDE_FIGS) or (c[0] == "table" and c[1][0] in WIDE_TABLES)
k = 1
while k < len(content):
    if is_wide(content[k]) and content[k - 1][0] in ("h1", "h2"):
        n = 2 if content[k][0] == "fig" and k + 1 < len(content) and content[k + 1][0] == "figcap" else 1
        hs = k - 1
        while hs - 1 >= 0 and content[hs - 1][0] in ("h1", "h2"):
            hs -= 1                                  # e.g. "IV. 결과" + "A. ..." both move below the float
        content[hs:k + n] = content[k:k + n] + content[hs:k]
        k += n
    k += 1
gen = []
k = 0
while k < len(content):
    kind, val = content[k]
    if kind == "h1":
        gen.append(para("1", inline(val)))
    elif kind == "h2":
        gen.append(para("2", inline(val)))
    elif kind == "refhead":
        gen.append(para("5", run("참고문헌")))
        for r in refs:
            gen.append(para("references", inline(r), '<w:ind w:start="17.70pt" w:hanging="17.70pt"/>'))
    elif kind == "p":
        gen.append(para("a3", inline(val)))
    elif kind == "fig":
        wide = val in WIDE_FIGS
        cap = content[k + 1][1] if k + 1 < len(content) and content[k + 1][0] == "figcap" else ""
        block = [image_para(val, 6.2 if wide else 3.3), para("figurecaption", inline(cap), "<w:keepLines/>")]
        gen += ([brk_two] + block + [brk_one]) if wide else block
        k += 2 if cap else 1
        continue
    elif kind == "table":
        num, cap, rows = val
        wide = num in WIDE_TABLES
        block = [para("tablehead", inline(cap), "<w:keepNext/>"), table(rows, TABLE_WIDTHS[num]),
                 para(None, "", '<w:spacing w:before="0pt" w:after="6pt"/>')]
        gen += ([brk_two] + block + [brk_one]) if wide else block
    k += 1

new_items = [p_title, items[2][1], items[3][1], p_auth, sect_auth, p_abs, p_kw] + gen + [items[86][1], "<w:p/>", items[88][1]]
x = x[:b] + "".join(new_items) + x[e:]
open(doc_path, "w", encoding="utf-8").write(x)

# media, relationships, content types
os.makedirs(f"{U}/word/media", exist_ok=True)
rels = open(f"{U}/word/_rels/document.xml.rels", encoding="utf-8").read()
for name, rid in IMG_IDS.items():
    shutil.copy(FIGS[name], f"{U}/word/media/{name.lower()}")
    if rid not in rels:
        rels = rels.replace("</Relationships>",
            f'<Relationship Id="{rid}" Type="http://purl.oclc.org/ooxml/officeDocument/relationships/image" Target="media/{name.lower()}"/></Relationships>')
open(f"{U}/word/_rels/document.xml.rels", "w", encoding="utf-8").write(rels)
ct = open(f"{U}/[Content_Types].xml", encoding="utf-8").read()
if 'Extension="png"' not in ct:
    ct = ct.replace("<Default Extension=\"xml\"", '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"')
open(f"{U}/[Content_Types].xml", "w", encoding="utf-8").write(ct)
print("headings", sum(1 for c in content if c[0] in ("h1", "h2")), "paragraphs", sum(1 for c in content if c[0] == "p"),
      "tables", sum(1 for c in content if c[0] == "table"), "figs", sum(1 for c in content if c[0] == "fig"), "refs", len(refs))
