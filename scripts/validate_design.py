"""Validate packaging and independent reference arithmetic, not application behavior."""
from pathlib import Path
from decimal import Decimal as D
import json, re, zipfile
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1]
errors=[]
mds=[p for p in ROOT.rglob('*.md') if 'documents' not in p.parts]
for p in mds:
 s=p.read_text()
 if sum(line.startswith('```') for line in s.splitlines())%2:errors.append(f'{p}: unbalanced fence')
 for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',s):
  if '://' not in target and not target.startswith(('#','mailto:')):
   if not (p.parent/target.split('#')[0]).exists():errors.append(f'{p}: missing {target}')
for p in (ROOT/'fixtures').glob('*.json'):json.loads(p.read_text())
season=json.loads((ROOT/'fixtures/season_scenario.json').read_text())
assert sum(D(x['capital']) for x in season['investors'])==D(season['opening']['fund_nav'])
assert sum(D(x['units']) for x in season['investors'])==D('250000')
assert season['clock']['chapters']*season['clock']['days_per_chapter']==season['clock']['business_days']
assert season['clock']['first_playable_days']==20
assert [c['end_day'] for c in season['chapters']]==[10,20,30,40,50,60]
assert season['dealing']['notice_days']==[x-5 for x in season['dealing']['days']]
assert season['stress_arithmetic_reference']['after']['maintenance_shortfall']=='112500.00'
golden=json.loads((ROOT/'fixtures/golden_scenario.json').read_text())
for state in golden['steps']:
 cash=D(state['settled_cash']);rec=D(state['receivable']);pay=D(state['payable'])
 holdings=D(str(state['quantity']))*D(state.get('mark','0'))
 if cash+rec+holdings-pay!=D(state['nav']):errors.append(f'legacy NAV: {state["event"]}')
assert D('100000')+D('80000')+D('70000')==D('250000')
assert D('250000')*100==D('25000000')
assert D('100')*(D('110')-100)*D('.2')==200
assert (D('11000')-200)/100==108
assert D('27.5')*D('.95')==D('26.125')
assert D('5')*D('1.10')==D('5.5')
assert D('25')-D('1.375')-D('.5')==D('23.125')
assert D('26.125')*D('.7')+D('5.5')*D('.9')-D('23.125')==D('.1125')
assert D('25')*D('.2')==D('5')
assert D('1.10')*D('.90')-1==D('-.01')
assert D('90')/120-1==D('-.25')
word=ROOT/'documents/FundForge_Project_Spec_and_Claude_Handoff.docx'
with zipfile.ZipFile(word) as z:
 assert z.testzip() is None
 xml=ElementTree.fromstring(z.read('word/document.xml'))
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 tables=len(xml.findall('.//w:tbl',ns));paras=len(xml.findall('.//w:p',ns))
 assert tables>=10 and paras>=100
from build_documents import SOURCES, markdown_links
combined=(ROOT/'documents/FundForge_Project_Spec_and_Claude_Handoff.md').read_text()
for p in SOURCES:
 if markdown_links((ROOT/p).read_text(),p) not in combined:errors.append(f'bundle out of date: {p}')
if errors:raise SystemExit('\n'.join(errors))
print(f'PASS: {len(mds)} Markdown files: fences/local links; JSON syntax; six legacy NAV states; independent capitalization/fees/margin/gate/return arithmetic; Word archive ({tables} tables, {paras} paragraphs); {len(SOURCES)} source sections agree with Markdown bundle.')
print('LIMIT: no application engine, PostgreSQL, gameplay, balance, provider, security, load or ML tests exist or were run.')
