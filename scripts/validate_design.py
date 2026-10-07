"""Validate packaging and independent reference arithmetic, not application behavior."""
from pathlib import Path
from decimal import Decimal as D, ROUND_HALF_EVEN, localcontext
from datetime import date, timedelta
import json, re, zipfile
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = 0

def check(actual, expected, label):
    global checks
    checks += 1
    if actual != expected:
        errors.append(f'{label}: expected {expected!r}; observed {actual!r}')

def dec_equal(actual, expected, label):
    check(D(actual), D(expected), label)

def rounded(value, scale='0.01'):
    return value.quantize(D(scale), rounding=ROUND_HALF_EVEN)

def load(name):
    return json.loads((ROOT/'fixtures'/name).read_text(encoding='utf-8'))

def dates(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return [a + timedelta(days=i) for i in range((b-a).days+1)]

mds = [p for p in ROOT.rglob('*.md') if 'documents' not in p.parts]
for p in mds:
    s = p.read_text(encoding='utf-8')
    check(sum(line.startswith('```') for line in s.splitlines()) % 2, 0, f'{p.name}: fences')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', s):
        if '://' not in target and not target.startswith(('#', 'mailto:')):
            check((p.parent/target.split('#')[0]).exists(), True, f'{p.name}: link {target}')
for p in (ROOT/'fixtures').glob('*.json'):
    json.loads(p.read_text(encoding='utf-8'))
season = load('season_scenario.json')
check(season['scenario_version'], '2.1.0', 'scenario version')
dec_equal(sum(D(x['capital']) for x in season['investors']), season['opening']['fund_nav'], 'LP capitalization')
dec_equal(sum(D(x['units']) for x in season['investors']), '250000', 'opening units')
clock = season['clock']
check(clock['chapters']*clock['days_per_chapter'], clock['business_days'], 'chapter length')
check(clock['first_playable_days'], 20, 'first playable length')
check([c['end_day'] for c in season['chapters']], [10,20,30,40,50,60], 'chapter ends')
check(season['dealing']['notice_days'], [x-5 for x in season['dealing']['days']], 'notice lead')
all_dates = dates(clock['first_business_date'], clock['day_61_date'])
workdays = [x for x in all_dates if x.weekday() < 5]
check(len(workdays), 61, 'synthetic business dates')
for index, key in [(20,'day_20_date'), (40,'day_40_date'), (60,'last_scored_business_date'), (61,'day_61_date')]:
    check(workdays[index-1].isoformat(), clock[key], key)
check(len(dates(clock['first_business_date'], clock['last_scored_business_date'])), clock['scored_calendar_accrual_dates'], 'scored accrual dates')
check(season['fees']['fundwide_performance_crystallization_within_launch_quarter'], False, 'no quarter-wide crystallization')
check(season['fees']['annual_crystallization_month_day'], '12-31', 'annual date')
check(season['fees']['partial_redemption_surviving_hwm_unchanged'], True, 'partial HWM contract')
check(season['prime_broker']['borrow_day_count'], 'ACT_360', 'borrow day count')
check(season['prime_broker']['debit_day_count'], 'ACT_360', 'debit day count')
check('365' in season['fees']['management_accrual_basis'], True, 'management day count')

# Six legacy states remain an isolated no-cost cash-account reference.
golden = load('golden_scenario.json')
for state in golden['steps']:
    nav = D(state['settled_cash'])+D(state['receivable'])+D(str(state['quantity']))*D(state.get('mark','0'))-D(state['payable'])
    dec_equal(nav, state['nav'], f'legacy NAV {state["event"]}')

case_file = load('scenario_cases.json')
check(case_file['executed_application_tests'], False, 'honest fixture status')
oracles = {x['id']:x for x in case_file['arithmetic_cases']}
check(len(oracles), 9, 'arithmetic case identity/count')
with localcontext() as ctx:
    ctx.prec = 40
    c = oracles['cohort_participation_before_reversible_provision']; e = c['expected']
    participation = [D(x['net_capital'])+D(x['provisional_fee']) for x in c['opening']]
    allocated = [D(c['common_pnl'])*a/sum(participation) for a in participation]
    closing = [a+p for a,p in zip(participation,allocated)]
    provisions = [D(c['performance_rate'])*max(D(0), b-D(s['hwm'])*D(s['units'])) for b,s in zip(closing,c['opening'])]
    net = [b-f for b,f in zip(closing,provisions)]
    for key, actual in [('participation_capital',participation),('common_pnl_allocated',allocated),('closing_pre_performance',closing),('closing_provision',provisions),('closing_net_capital',net)]:
        check(actual, [D(x) for x in e[key]], f'cohort {key}')
    dec_equal(sum(net),e['fund_nav'],'cohort sum NAV')
    c = oracles['partial_redemption_preserves_surviving_hwm']; e = c['expected']
    u,h,b,r,q = (D(c[x]) for x in ['units','hwm','pre_performance_capital','performance_rate','redeem_units'])
    f=max(D(0),b-u*h)*r; n=b-f; fraction=q/u
    actual = {'provision_before':f,'net_before':n,'redemption_payable':n*fraction,'crystallized_fee':f*fraction,'remaining_units':u-q,'remaining_provision':f*(1-fraction),'remaining_net_capital':n*(1-fraction),'remaining_hwm':h}
    for k,v in actual.items(): dec_equal(v,e[k],f'partial redemption {k}')
    dec_equal(actual['remaining_net_capital']+actual['redemption_payable']+actual['remaining_provision']+actual['crystallized_fee'], b, 'claims conserved')
    c = oracles['redemption_shrinks_risk_equity']; e=c['expected']
    n,l,s,r=(D(c[x]) for x in ['nav','long_mv','short_mv','dealt_redemption'])
    for k,v in {'pre_gross':(l+s)/n,'pre_net':(l-s)/n,'post_nav':n-r,'post_gross':(l+s)/(n-r),'post_net':(l-s)/(n-r),'payment_nav_change':D(0)}.items():dec_equal(v,e[k],f'redemption risk {k}')
    c=oracles['cover_increases_net_after_costs'];e=c['expected']
    n=D(c['nav'])-D(c['cost']);l=D(c['long_mv']);s=D(c['short_mv'])-D(c['cover_reference']);net=(l-s)/n
    for k,v in {'post_nav':n,'post_long':l,'post_short':s,'net_rounded_12dp':rounded(net,'0.000000000001')}.items():dec_equal(v,e[k],f'cover {k}')
    check(net>D(c['net_max']), e['net_cap_breached'], 'cover directional breach')
    c=oracles['calendar_fee_constant_base'];e=c['expected'];count=D(c['calendar_dates'])
    mgmt=D(c['management_base'])*D(c['management_rate'])/D(c['management_basis'])
    values={'management_one_date_posting':rounded(mgmt),'management_three_dates_total_posting':rounded(mgmt*count),'debit_one_date':rounded(D(c['debt'])*D(c['debit_rate'])/D(c['debit_basis'])),'borrow_three_dates_total_posting':rounded(D(c['borrow_reference'])*D(c['borrow_rate'])/D(c['borrow_basis'])*count)}
    for k,v in values.items():dec_equal(v,e[k],f'calendar accrual {k}')
    c=oracles['short_distribution_and_fee_reversal'];e=c['expected']
    b=D(c['pre_correction_pre_performance_capital']);h=D(c['hwm'])*D(c['units']);r=D(c['performance_rate']);liability=D(c['short_quantity'])*D(c['distribution_per_share']);old=max(D(0),b-h)*r;new=max(D(0),b-liability-h)*r
    values={'missing_payable':liability,'pre_correction_provision':old,'corrected_pre_performance_capital':b-liability,'corrected_provision':new,'provision_reversal':old-new,'corrected_net_nav':b-liability-new,'net_nav_correction':-liability+old-new}
    for k,v in values.items():dec_equal(v,e[k],f'distribution correction {k}')
    c=oracles['distribution_total_return'];e=c['expected'];p=D(c['quantity'])*(D(c['ex_price'])-D(c['cum_price']));income=D(c['quantity'])*D(c['distribution_per_share'])
    for k,v in {'long_price_pnl':p,'long_income':income,'short_price_pnl':-p,'short_distribution_expense':-income,'long_total_pnl':p+income,'short_total_pnl':-p-income}.items():dec_equal(v,e[k],f'total return {k}')
    c=oracles['borrow_weekend_lifecycle'];e=c['expected'];charged=dates(c['short_settlement_date'],c['return_settlement_date'])[:-1]
    check([x.isoformat() for x in charged],e['charged_calendar_dates'],'borrow settled interval')
    check(any(x.isoformat()==c['return_settlement_date'] for x in charged),e['return_date_charged'],'borrow endpoint')
    check([x.isoformat() for x in dates(c['short_trade_date'],c['short_settlement_date'])[:-1] if x in charged],e['pre_settlement_weekend_borrow_dates'],'borrow begins on settlement')
    c=oracles['terminal_calendar_boundary'];e=c['expected'];scored=dates(c['day_1'],c['day_60'])
    check(len(scored),e['scored_calendar_dates'],'terminal calendar count')
    check(sum(x.weekday()<5 for x in scored),e['scored_business_days'],'terminal business count')
    check([x.isoformat() for x in dates(c['day_60'],c['day_61'])[1:-1]],e['additional_accrual_dates_before_checkpoint'],'terminal weekend dates')

    episodes={x['id']:x for x in case_file['cases']};check(len(episodes),3,'three episode contracts')
    one=episodes['case_1_borrow_not_thesis'];a=one['opening'];shock=one['shock_reference']
    dec_equal(D(a['cash'])+D(a['restricted_cash'])+D(a['long_mv'])-D(a['short_mv'])-D(a['broker_debt']),a['nav'],'case1 balance')
    required=D(shock['long_mv'])*D(shock['maintenance_long'])+D(shock['short_mv'])*D(shock['maintenance_short'])
    dec_equal(required,shock['maintenance_required'],'case1 maintenance')
    dec_equal(required-D(shock['nav']),shock['shortfall'],'case1 margin gap')
    for b in one['expected_response_branches']:
        if b['id']=='replacement_only':
            dec_equal(rounded(D(b['replacement_reference'])*D(b['replacement_rate'])/360,'0.000000000001'),b['calendar_day_borrow_cost_12dp'],'replacement borrow')
            continue
        q=D(b['quantity']);ref=D(95 if b['id']=='sell_liquid_long' else 110)
        price=ref*(D('.999') if b['id']=='sell_liquid_long' else D('1.001'))
        dec_equal(price,b['execution_price'],'case1 actual price')
        dec_equal(q*ref,b['reference_reduction'],'case1 reference reduction')
        cost=abs(q*(price-ref));dec_equal(cost,b['cost'],'case1 execution cost')
        nav=D(shock['nav'])-cost
        coef=D(shock['maintenance_long'] if b['id']=='sell_liquid_long' else shock['maintenance_short'])
        req=required-q*ref*coef
        dec_equal(nav,b['nav'],'case1 post-fill NAV');dec_equal(req,b['maintenance_required'],'case1 post-fill maintenance');dec_equal(nav-req,b['maintenance_headroom'],'case1 headroom')
    two=episodes['case_2_profitable_illiquid_redeeming'];a=two['opening_comparison'];qte=two['quote']
    basket=two['opening_positions']
    check(sum(D(p['quantity'])*D(p['reference']) for p in basket if p['side']=='LONG'),D(a['long_mv']),'case2 complete long basket')
    check(sum(D(p['quantity'])*D(p['reference']) for p in basket if p['side']=='SHORT'),D(a['short_mv']),'case2 complete short basket')
    dec_equal(D(a['cash'])+D(a['restricted_cash'])+D(a['long_mv'])-D(a['short_mv'])-D(a['broker_debt'])-D(a['fixed_invoice']),a['nav'],'case2 balance')
    for b in two['expected_branches']:
        q=D(b['sell_quantity']);ref=D(qte['reference']);vol=D(qte['volume'])
        check(q<=vol*D(qte['participation']),True,'case2 capacity')
        price=rounded(ref*(1-(D(qte['half_spread_bps'])+D(qte['impact_coefficient_bps'])*(q/vol)**2)/10000),'0.000001')
        proceeds=rounded(q*price);cost=q*ref-proceeds;pre=D(a['nav'])-cost
        dealt=sum(D(x) for x in a['equal_dollar_requests']) if b['id']=='pay_all' else rounded(pre*D(season['dealing']['optional_gate_nav_fraction']))
        values={'execution_price':price,'sale_proceeds':proceeds,'cost':cost,'pre_flow_nav':pre,'dealt':dealt,'post_flow_nav':pre-dealt,'post_long_mv':D(a['long_mv'])-q*ref,'post_short_mv':D(a['short_mv']),'payment_cash':D(a['cash'])+proceeds-dealt-D(a['fixed_invoice']),'deferred_each':D(a['equal_dollar_requests'][0])-dealt/2}
        for k,v in values.items():dec_equal(v,b[k],f'case2 {b["id"]} {k}')
        check((values['post_long_mv']+values['post_short_mv'])/values['post_flow_nav']<=D(season['mandate']['gross_max']),True,'case2 gross')
        check((values['post_long_mv']-values['post_short_mv'])/values['post_flow_nav']<=D(season['mandate']['net_max']),True,'case2 net')
        for p in basket:
            if p['instrument'] not in ('BEAM','BOND'):
                cap=D('.15') if p['side']=='LONG' else D('.08')
                check(D(p['quantity'])*D(p['reference'])/values['post_flow_nav']<=cap,True,f'case2 issuer {p["instrument"]}/{b["id"]}')
        sectors=[('ALTO','BRIN'),('COVE','DART'),('ELAN','FENN'),('GALA','HELI'),('IONA','JUNO')]
        for ids in sectors:
            gross=sum(D(p['quantity'])*D(p['reference']) for p in basket if p['instrument'] in ids)
            check(gross/values['post_flow_nav']<=D('.35'),True,f'case2 sector {ids}/{b["id"]}')
        check(D('3000000')/values['post_flow_nav']>D('.15'),True,'old inherited issuer basket fails')
        check(values['post_long_mv']*D('.5')+values['post_short_mv']*D('.6')<=values['post_flow_nav'],True,'case2 initial margin')
        check(values['payment_cash']>=0,True,'case2 normalized cash solvent')
        check((D('8000000')-q*ref)/values['post_flow_nav']<=D('.5'),True,'case2 BEAM cap')
        check(D('2500000')/values['post_flow_nav']<=D('.5'),True,'case2 BOND cap')
    three=episodes['case_3_balanced_but_wrong_nav'];a=three['company'];start=D(a['opening_cash']);weekly=D(a['baseline_weekly_cost']);receipt=D(a['management_fee_receivable_due_day41'])
    f=three['fund_opening']
    dec_equal(D(f['cash'])+D(f['restricted_cash'])+D(f['long_mv'])-D(f['short_mv'])-D(f['fixed_management_fee_payable'])-D(f['provisional_performance_fee']), f['net_nav'], 'case3 fund balance includes fixed fee')
    dec_equal(f['fixed_management_fee_payable'],a['management_fee_receivable_due_day41'],'case3 inter-entity claim match')
    check(season['mandate']['issuer_cap_scope'],'SINGLE_NAME_EQUITIES','issuer versus ETF scope')
    check(D(f['short_mv'])/D(f['net_nav'])<=D(season['mandate']['diversified_etf_max']),True,'case3 ETF cap')
    for b in three['expected_company_branches']:
        hire=b['id']=='hire_operations';d30=start-weekly-(D(a['ops_recruitment']) if hire else 0);burn=weekly+(D(a['ops_extra_weekly_cost']) if hire else 0);d35=d30-burn;d40=d35-burn;arrears=max(D(0),-d40);d41=max(D(0),d40)+receipt-arrears
        for k,v in {'day30_cash':d30,'day35_cash':d35,'day40_cash':max(D(0),d40),'day41_cash':d41,'weekly_cost':burn}.items():dec_equal(v,b[k],f'case3 {b["id"]} {k}')
        key='runway_weeks_12dp' if hire else 'runway_weeks';dec_equal(rounded(d41/burn,'0.000000000001'),b[key],'case3 runway')
        if hire:dec_equal(arrears,b['day40_unpaid_payroll'],'company arrears')
    check(three['expected_company_branches'][1]['active_gameplay_choice'],False,'dominated hire excluded')
    check(two['evaluation_horizon_v2_2'],[39,61],'gate evaluation continues through payment')
    residual=D(0);posted=D(0)
    expected_residuals=['-0.004444444444444444444444','0.001111111111111111111112','-0.003333333333333333333332']
    for expected in expected_residuals:
        accrual=D('1000000')*D('.02')/360
        today=rounded(residual+accrual)
        residual=rounded(residual+accrual-today,'0.000000000000000000000001')
        posted+=today
        dec_equal(residual,expected,'v2.2 residual recurrence')
    dec_equal(posted,'166.67','v2.2 carried three-date total')
    dec_equal(rounded(D('0.0000000000000000000000005'),'0.000000000000000000000001'),'0','residual HALF_EVEN tie')

    route=one['continuation_feasibility']
    before=D(one['expected_response_branches'][0]['nav'])-D('1900')
    required=D(one['expected_response_branches'][0]['maintenance_required'])-D('20000')*D('95')*D(shock['maintenance_long'])
    after=(before-D(route['max_additional_charges_bound']))*(1-D(route['tactical_units_fraction']))
    dec_equal(before,route['long_sale_branch_pre_charges_nav'],'case1 continuation NAV')
    dec_equal(required,route['long_sale_branch_maintenance'],'case1 continuation maintenance')
    dec_equal(rounded(after),route['post_redemption_nav_lower_bound'],'case1 post-flow bound')
    dec_equal(rounded(after-required),route['maintenance_headroom_lower_bound'],'case1 headroom bound')

review=load('library_review.json');candidates=review['candidates']
check(len(candidates),17,'library count');check(len({x['id'] for x in candidates}),17,'unique libraries')
for c in candidates:
    for key in ['snapshot','license_blob_sha','evidence_blob_sha']:
        check(bool(re.fullmatch(r'[0-9a-f]{40}',c[key])),True,f'{c["id"]} {key}')
    for key in ['license_url','evidence_url']:
        check(c[key].startswith('https://github.com/'+c['repository']+'/blob/'+c['snapshot']+'/'),True,f'{c["id"]} pinned {key}')
    check(c['recommendation']!='',True,f'{c["id"]} recommendation')

# Validate planning coverage only; this is not milestone execution evidence.
roadmap=(ROOT/'docs/IMPLEMENTATION_PLAN.md').read_text(encoding='utf-8')
packages=(ROOT/'docs/MILESTONE_PLANS.md').read_text(encoding='utf-8')
roadmap_rows=[line.split('|')[1:5] for line in roadmap.splitlines() if re.match(r'^\| FF\d[a-z]?:',line)]
roadmap_ids=[re.match(r'\s*(FF\d[a-z]?):',row[0]).group(1) for row in roadmap_rows]
headers=list(re.finditer(r'^## (FF\d[a-z]?)\s+—',packages,re.M))
package_ids=[match.group(1) for match in headers]
check(len(roadmap_ids),20,'twenty roadmap milestones')
check(len(set(roadmap_ids)),20,'unique roadmap milestones')
check(package_ids,roadmap_ids,'detailed plans cover all roadmap milestones in order')
for index,header in enumerate(headers):
    section=packages[header.start():headers[index+1].start() if index+1<len(headers) else len(packages)]
    for field in ['**Purpose and value.**','**Entry / inputs.**','**Ownership / outputs.**','**Ordered tasks','**Acceptance / verification.**','**Failure and stop.**']:
        check(field in section,True,f'{header.group(1)} full work-package field {field}')
    check(bool(re.search(r'^1\. ',section,re.M)),True,f'{header.group(1)} ordered execution tasks')
dependencies={identifier:re.findall(r'FF\d[a-z]?',row[1]) for identifier,row in zip(roadmap_ids,roadmap_rows)}
visited=set(); active=set()
def visit(identifier):
    if identifier in active:
        raise ValueError(f'Milestone dependency cycle at {identifier}')
    if identifier in visited: return
    active.add(identifier)
    for dependency in dependencies[identifier]:
        if dependency not in dependencies:
            raise ValueError(f'Unknown dependency {dependency} for {identifier}')
        visit(dependency)
    active.remove(identifier); visited.add(identifier)
for identifier in roadmap_ids: visit(identifier)
check(len(visited),20,'milestone dependency graph acyclic and complete')
# Conditional historical-data prerequisite is checked conservatively for cycles.

from build_documents import SOURCES, markdown_links
combined=(ROOT/'documents/FundForge_Project_Spec_and_Claude_Handoff.md').read_text(encoding='utf-8')
for p in SOURCES:
    check(markdown_links((ROOT/p).read_text(encoding='utf-8'),p) in combined,True,f'bundle current: {p}')
word=ROOT/'documents/FundForge_Project_Spec_and_Claude_Handoff.docx'
with zipfile.ZipFile(word) as z:
    check(z.testzip(),None,'Word archive')
    xml=ElementTree.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    tables=len(xml.findall('.//w:tbl',ns));paras=len(xml.findall('.//w:p',ns))
    word_text='\n'.join(''.join(p.itertext()) for p in xml.findall('.//w:p',ns))
    for path in SOURCES:
        check(path in word_text,True,f'Word source: {path}')
    check(tables>=10 and paras>=100,True,'Word nonempty structure')
    if 'source_manifest.json' in z.namelist():
        import hashlib
        manifest=json.loads(z.read('source_manifest.json'))
        check(manifest,{p:hashlib.sha256((ROOT/p).read_text(encoding='utf-8').encode('utf-8')).hexdigest() for p in SOURCES},'Word exact source hashes')
        for name in z.namelist():
            if name.endswith(('.xml','.rels')):
                ElementTree.fromstring(z.read(name))
        # Check visible text, not only a manifest that could accompany stale content.
        actual_paras=[''.join(p.itertext()) for p in xml.findall('.//w:p',ns)]
        for path in SOURCES:
            for line in (ROOT/path).read_text(encoding='utf-8').splitlines():
                if not line.strip() or line.startswith('```') or line=='---' or re.fullmatch(r'\|[ :|\-]+\|',line): continue
                values=[x.strip() for x in line.strip('|').split('|')] if line.startswith('|') else [re.sub(r'^#{1,6}\s+','',line)]
                for value in values:
                    visible=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1',value.replace('**','').replace('`',''))
                    check(visible in actual_paras,True,f'Word visible source text: {path}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {checks} packaging/reference checks; {len(mds)} source Markdown files; {len(SOURCES)} bundled sections; {tables} Word tables/{paras} paragraphs; 9 arithmetic oracles, 3 episode checkpoint contracts, 17 pinned repository records.')
print('LIMIT: no simulation runtime or application acceptance, PostgreSQL race, gameplay/balance, provider, security, load or ML tests exist or ran. No Word page-render inspection.')
