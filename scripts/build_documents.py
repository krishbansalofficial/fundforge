"""Regenerate documentation; python-docx optional, standard-library OOXML fallback."""
from pathlib import Path
import re
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
except ModuleNotFoundError as exc:
    if exc.name != 'docx':
        raise
    Document = None

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
 'README.md','docs/REALISM_AUDIT.md','docs/MASTER_SPEC.md','docs/GAME_SYSTEMS.md',
 'docs/SEASON_SCENARIOS.md','docs/FUND_ACCOUNTING.md',
 'docs/LIBRARY_RESEARCH.md',
 'docs/SIMULATION_ARCHITECTURE.md','docs/IMPLEMENTATION_PLAN.md',
 'docs/ACCEPTANCE_TESTS.md','docs/DECISIONS.md','docs/CLAUDE_HANDOFF.md',
 'docs/PROMPT_PACK.md','docs/AGENT_WORKFLOW.md','docs/RECRUITER_EVIDENCE.md',
 'docs/SOURCES.md','docs/PROGRESS.md','docs/PACKAGING_VALIDATION.md',
 'docs/DESIGN_REVIEW_V2_2.md','docs/SCENARIO_CONTRACTS.md',
 'docs/IMPLEMENTATION_HANDOFF.md','docs/PLAN_REVIEW_AND_DECISIONS.md',
 'docs/MILESTONE_PLANS.md'
]
BASE = ROOT/'documents/FundForge_Project_Spec_and_Claude_Handoff'

def inline(p, text, source):
    """Keep source links clickable; resolve repo-relative links for the bundle."""
    text=text.replace('**','').replace('`','')
    at=0
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)',text):
        p.add_run(text[at:m.start()])
        label,url=m.groups()
        if not re.match(r'https?://',url):
            target=(ROOT/source).parent/url
            url='https://github.com/krishbansalofficial/fundforge/blob/main/'+str(target.resolve().relative_to(ROOT.resolve()))
        link=OxmlElement('w:hyperlink')
        link.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
        run=OxmlElement('w:r'); props=OxmlElement('w:rPr')
        color=OxmlElement('w:color');color.set(qn('w:val'),'175B89');props.append(color)
        run.append(props);t=OxmlElement('w:t');t.text=label;run.append(t);link.append(run);p._p.append(link)
        at=m.end()
    p.add_run(text[at:])

def markdown_links(text,source):
    def rewrite(m):
        label,url=m.groups()
        if re.match(r'https?://',url): return m.group(0)
        target=((ROOT/source).parent/url).resolve().relative_to(ROOT.resolve())
        return f'[{label}](https://github.com/krishbansalofficial/fundforge/blob/main/{target})'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',rewrite,text)

def build():
    texts=[(p,(ROOT/p).read_text(encoding='utf-8')) for p in SOURCES]
    combined='# FundForge — complete design and implementation handoff\n\nVersion 2.2 · 7 October 2026 · Design package; application unimplemented.\n\n'
    combined+='Generated from canonical repository documents. Edit the sources and rerun scripts/build_documents.py.\n\n'
    for p,s in texts:
        combined+=f'\n---\n\nSource: `{p}`\n\n'+markdown_links(s,p)+'\n'
    BASE.with_suffix('.md').write_text(combined, encoding='utf-8')
    if Document is None:
        build_word_stdlib(texts)
        print(f'Generated Markdown and Word from {len(SOURCES)} sources (standard-library OOXML; rendering unverified)')
        return
    doc=Document(); sec=doc.sections[0]
    sec.top_margin=sec.bottom_margin=Inches(.7)
    sec.left_margin=sec.right_margin=Inches(.7)
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(5)
    for st in ['Heading 1','Heading 2','Heading 3']:
        doc.styles[st].font.color.rgb=RGBColor.from_string('17435B')
    doc.add_heading('FundForge',0)
    doc.add_paragraph('A cooperative hedge-fund management strategy game',style='Subtitle')
    doc.add_paragraph('Design v2.2 | 7 October 2026')
    doc.add_paragraph('Two partners. Investor capital. Financing pressure. A firm worth keeping alive.')
    doc.add_paragraph('Specification and implementation handoff. This package defines proposed behavior; no application, provider integration or model is implemented.')
    doc.add_heading('Document map',1)
    for p,_ in texts:
        doc.add_paragraph(p,style='List Bullet')
    footer=sec.footer.paragraphs[0];footer.alignment=2
    footer.add_run('FundForge v2.2 | ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for source,text in texts:
        doc.add_page_break();doc.add_paragraph(source,style='Caption')
        lines=text.splitlines();i=0;code=False
        while i<len(lines):
            line=lines[i]
            if line.startswith('```'):
                code=not code;i+=1;continue
            if code:
                p=doc.add_paragraph();run=p.add_run(line);run.font.name='Consolas';run.font.size=Pt(8);i+=1;continue
            if not line.strip(): i+=1;continue
            if line.startswith('|') and i+1<len(lines) and re.match(r'^\|[ :|\-]+\|$',lines[i+1]):
                rows=[line];i+=2
                while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
                cells=[[x.strip() for x in row.strip('|').split('|')] for row in rows]
                table=doc.add_table(rows=1,cols=len(cells[0]));table.style='Light Shading Accent 1'
                header=OxmlElement('w:tblHeader');header.set(qn('w:val'),'true')
                table.rows[0]._tr.get_or_add_trPr().append(header)
                for ri,row in enumerate(cells):
                    tc=table.rows[0].cells if ri==0 else table.add_row().cells
                    for ci,value in enumerate(row):inline(tc[ci].paragraphs[0],value,source)
                continue
            h=re.match(r'^(#{1,6})\s+(.+)',line)
            if h:doc.add_heading(h.group(2),min(len(h.group(1)),4));i+=1;continue
            if line=='---':i+=1;continue
            bullet=re.match(r'^[-*]\s+(.+)',line);number=re.match(r'^\d+\.\s+(.+)',line)
            p=doc.add_paragraph(style='List Bullet' if bullet else 'List Number' if number else None)
            inline(p,(bullet or number).group(1) if bullet or number else line,source);i+=1
    doc.save(BASE.with_suffix('.docx'))
    print(f'Generated {BASE.with_suffix(".md").name} and .docx from {len(SOURCES)} sources')

def build_word_stdlib(texts):
    """Original minimal OOXML writer for docs only, without package installation."""
    import zipfile, hashlib, json
    from xml.sax.saxutils import escape, quoteattr
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    relationships = []

    def runs(value, source):
        value = value.replace('**', '').replace('`', '')
        def run(s):
            return '<w:r><w:t xml:space="preserve">'+escape(s)+'</w:t></w:r>'
        result = []; at = 0
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', value):
            result.append(run(value[at:match.start()]))
            label, url = match.groups()
            if not re.match(r'https?://', url):
                target = ((ROOT/source).parent/url).resolve().relative_to(ROOT.resolve())
                url = 'https://github.com/krishbansalofficial/fundforge/blob/main/'+target.as_posix()
            key = f'link{len(relationships)+1}'
            relationships.append((key, url))
            result.append(f'<w:hyperlink r:id="{key}">'+run(label)+'</w:hyperlink>')
            at = match.end()
        result.append(run(value[at:]))
        return ''.join(result)

    def para(value, source, style=None):
        props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
        return '<w:p>'+props+runs(value, source)+'</w:p>'

    body = [para('FundForge v2.2 | 7 October 2026', 'README.md', 'Heading1'),
            para('Design and implementation handoff; application unimplemented.', 'README.md')]
    for source, text in texts:
        body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        body.append(para(source, source, 'Heading2'))
        lines=text.splitlines(); i=0; code=False
        while i < len(lines):
            line=lines[i]
            if line.startswith('```'):
                code=not code; i+=1; continue
            if not line.strip() or line=='---': i+=1; continue
            if not code and line.startswith('|') and i+1<len(lines) and re.match(r'^\|[ :|\-]+\|$',lines[i+1]):
                rows=[line]; i+=2
                while i<len(lines) and lines[i].startswith('|'): rows.append(lines[i]); i+=1
                count=len(rows[0].strip('|').split('|'))
                table=['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="autofit"/></w:tblPr>',
                       '<w:tblGrid>'+('<w:gridCol w:w="2000"/>'*count)+'</w:tblGrid>']
                for n,row in enumerate(rows):
                    cells=[v.strip() for v in row.strip('|').split('|')]
                    if len(cells)!=count: raise ValueError(f'Ragged table: {source}: {row}')
                    table.append('<w:tr>'+('<w:trPr><w:tblHeader/></w:trPr>' if n==0 else ''))
                    for cell in cells:
                        table.append('<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>'+para(cell,source)+'</w:tc>')
                    table.append('</w:tr>')
                table.append('</w:tbl>'); body.extend(table); continue
            heading=re.match(r'^(#{1,6})\s+(.+)',line)
            if heading and not code:
                body.append(para(heading.group(2),source,'Heading'+str(min(len(heading.group(1)),3))))
            else:
                body.append(para(line,source,'Code' if code else None))
            i+=1
    body.append('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1008" w:bottom="1008" w:left="1008" w:right="1008"/></w:sectPr>')
    declaration='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    document=declaration+f'<w:document xmlns:w="{w}" xmlns:r="{r}"><w:body>'+''.join(body)+'</w:body></w:document>'
    styles=declaration+f'<w:styles xmlns:w="{w}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="20"/></w:rPr></w:rPrDefault></w:docDefaults>'
    for n in range(1,4):
        styles+=f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/><w:pPr><w:keepNext/><w:outlineLvl w:val="{n-1}"/></w:pPr><w:rPr><w:b/><w:color w:val="17435B"/><w:sz w:val="{32-n*2}"/></w:rPr></w:style>'
    styles+='<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="16"/></w:rPr></w:style></w:styles>'
    rel_ns='http://schemas.openxmlformats.org/package/2006/relationships'
    doc_rels=declaration+f'<Relationships xmlns="{rel_ns}"><Relationship Id="styles" Type="{r}/styles" Target="styles.xml"/>'
    for key,url in relationships:
        doc_rels+=f'<Relationship Id="{key}" Type="{r}/hyperlink" Target={quoteattr(url)} TargetMode="External"/>'
    doc_rels+='</Relationships>'
    types=declaration+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="json" ContentType="application/json"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
    root_rels=declaration+f'<Relationships xmlns="{rel_ns}"><Relationship Id="main" Type="{r}/officeDocument" Target="word/document.xml"/></Relationships>'
    manifest={source:hashlib.sha256(text.encode('utf-8')).hexdigest() for source,text in texts}
    with zipfile.ZipFile(BASE.with_suffix('.docx'),'w',zipfile.ZIP_DEFLATED) as package:
        for name,content in {'[Content_Types].xml':types,'_rels/.rels':root_rels,'word/document.xml':document,'word/styles.xml':styles,'word/_rels/document.xml.rels':doc_rels,'source_manifest.json':json.dumps(manifest,sort_keys=True)}.items():
            package.writestr(name,content.encode('utf-8'))

if __name__=='__main__':build()
