"""Regenerate the review bundle from canonical docs. Requires python-docx."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
 'README.md','docs/REALISM_AUDIT.md','docs/MASTER_SPEC.md','docs/GAME_SYSTEMS.md',
 'docs/SEASON_SCENARIOS.md','docs/FUND_ACCOUNTING.md',
 'docs/LIBRARY_RESEARCH.md','docs/OPENSEO_INTEGRATION.md',
 'docs/SIMULATION_ARCHITECTURE.md','docs/IMPLEMENTATION_PLAN.md',
 'docs/ACCEPTANCE_TESTS.md','docs/DECISIONS.md','docs/CLAUDE_HANDOFF.md',
 'docs/PROMPT_PACK.md','docs/AGENT_WORKFLOW.md','docs/RECRUITER_EVIDENCE.md',
 'docs/SOURCES.md','docs/PROGRESS.md','docs/PACKAGING_VALIDATION.md'
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
    texts=[(p,(ROOT/p).read_text()) for p in SOURCES]
    combined='# FundForge — complete design and implementation handoff\n\nVersion 2.1 · 6 October 2026 · Design package; application unimplemented.\n\n'
    combined+='Generated from canonical repository documents. Edit the sources and rerun scripts/build_documents.py.\n\n'
    for p,s in texts:
        combined+=f'\n---\n\nSource: `{p}`\n\n'+markdown_links(s,p)+'\n'
    BASE.with_suffix('.md').write_text(combined)
    doc=Document(); sec=doc.sections[0]
    sec.top_margin=sec.bottom_margin=Inches(.7)
    sec.left_margin=sec.right_margin=Inches(.7)
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(5)
    for st in ['Heading 1','Heading 2','Heading 3']:
        doc.styles[st].font.color.rgb=RGBColor.from_string('17435B')
    doc.add_heading('FundForge',0)
    doc.add_paragraph('A cooperative hedge-fund management strategy game',style='Subtitle')
    doc.add_paragraph('Design v2.1 | 6 October 2026')
    doc.add_paragraph('Two partners. Investor capital. Financing pressure. A firm worth keeping alive.')
    doc.add_paragraph('Specification and implementation handoff. This package defines proposed behavior; no application, provider integration or model is implemented.')
    doc.add_heading('Document map',1)
    for p,_ in texts:
        doc.add_paragraph(p,style='List Bullet')
    footer=sec.footer.paragraphs[0];footer.alignment=2
    footer.add_run('FundForge v2.1 | ')
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

if __name__=='__main__':build()
