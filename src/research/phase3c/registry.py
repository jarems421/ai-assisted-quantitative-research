"""Current official documentation review, separate from API/source certification."""
import json
from src.research.phase3c.sources import DOCS, RAW


def registry():
    common = {'review_date': '2026-10-12', 'personal_payment': 'NONE_AUTHORIZED_OR_PERFORMED',
              'documentation_access': 'Official pages reviewed through browser; original archive coverage recorded separately'}
    sources = [
        dict(common, name='SEC EDGAR', role='PRIMARY_SOURCE', authority='Original filing/issuer disclosure; not historical tradable class intervals',
             purpose='Original annual revenue and dated issuer/class/lifecycle evidence; structured submissions discovery only',
             documentation=['https://www.sec.gov/about/developer-resources', 'https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data'],
             authentication='Identified local EDGAR_IDENTITY; never tracked', free_tier='Public identified automated access',
             documented_rate='SEC fair access ceiling10requests/second; pilot single worker<=2starts/second',
             enforced_rate='0.55seconds/start, <=600starts total across preserved source attempts',
             fields=['accession', 'issuerCIK', 'form', 'filingDate', 'original XBRL', 'original cover/statement/lifecycle documents'],
             pit_limitations='Modern retrieved bytes are retrospective reconstruction; first website public instant unknown; discovery aggregates are not original reported facts',
             lifecycle_limitations='Cover pages are point observations; ending form alone does not certify terminal consideration',
             licensing='Public SEC source; preserve issuer document attribution and notices; raw originals ignored',
             authoritative_for='Exact archived issuer filings only'),
        dict(common, name='OpenFIGI', role='PRIMARY_SOURCE', authority='Identifier authority; current metadata not dated listing certificate',
             purpose='FIGI/composite/share-class identifier candidates, including unlisted equity results',
             documentation=['https://www.openfigi.com/api/documentation', 'https://www.openfigi.com/docs/terms-of-service'],
             authentication='Unauthenticated permitted; optional local OPENFIGI_API_KEY absent during pilot',
             free_tier='Free documented public mapping API', documented_rate='No-key25requests/minute; jobs/request inconsistent5vs10within same official page',
             enforced_rate='Conservative5jobs/request,>=3seconds/start, <=15requests total',
             fields=['figi', 'compositeFIGI', 'shareClassFIGI', 'ticker', 'exchCode', 'securityType', 'marketSector'],
             pit_limitations='No effective historical interval inferred from current response; ticker reuse/class multiplicity retained',
             lifecycle_limitations='Unlisted equities must explicitly be included; no terminal consideration or position-transition certificate',
             licensing='Review official terms; metadata/bodies remain ignored; public report publishes status/hashes only',
             authoritative_for='Returned identifier metadata only; not historical class ownership/listing spans'),
        dict(common, name='Tiingo EOD', role='PRIMARY_SOURCE', authority='Market-data vendor, not issuer lifecycle authority',
             purpose='Frozen-cohort2019–2020 raw daily price/action schema and coverage QA only',
             documentation=['https://www.tiingo.com/documentation/end-of-day', 'https://www.tiingo.com/about/pricing',
                            'https://www.tiingo.com/documentation/general/connecting', 'https://app.tiingo.com/tos/'],
             authentication='Local TIINGO_API_KEY configured by owner during Phase3C; header only',
             free_tier='Published Starter$0/month; account entitlement/billing not independently certified; no upgrade/purchase',
             documented_rate='50requests/hour,1000/day,500unique symbols/month,1GB/month',
             enforced_rate='<=50rolling starts/hour,<=1000/day,<=120pilot requests,<=60symbols; project monthly bandwidth bounded, other account activity unknown',
             fields=['rawOHLC', 'volume', 'divCash', 'splitFactor', 'adjusted fields', 'metadata start/end coverage'],
             pit_limitations='Modern revised/adjusted prices not historical ingestion vintage; metadata start/end are data coverage, not listing spans',
             lifecycle_limitations='Split/dividend fields do not certify merger, spinoff, cancellation or delisting recovery',
             licensing='Official pricing/terms restrict internal use; no vendor prices/metadata/payloads committed or redistributed',
             authoritative_for='Archived vendor observations within certified bindings, once proved; current QA alone is insufficient'),
        dict(common, name='Financial Modeling Prep', role='SECONDARY_CROSS_CHECK', authority='Discovery cross-check, never overrides primary sources',
             purpose='Optional delisted-company agreement/disagreement check',
             documentation=['https://site.financialmodelingprep.com/developer/docs/stable/delisted-companies',
                            'https://site.financialmodelingprep.com/developer/docs/pricing'],
             authentication='Local FMP_API_KEY absent; no API request', free_tier='Basic$0; endpoint-specific delisted entitlement unverified',
             documented_rate='250calls/day and500MBtrailing30day bandwidth on official pricing', enforced_rate='0APIcalls; no unauthenticated entitlement guessed',
             fields=[], pit_limitations='Present delisted directory not original PIT issuer disclosure',
             lifecycle_limitations='No sole historical-price or terminal-value authority',
             licensing='Display/redistribution needs separate agreement; do not publish vendor payloads', authoritative_for='None in pilot'),
        dict(common, name='Loughborough / Orbis', role='SECONDARY_CROSS_CHECK', authority='Optional owner-supplied independent manual check',
             purpose='Resolve specifically named class/span/terminal ambiguity',
             documentation=['https://www.lboro.ac.uk/services/library/databases/'], authentication='Owner university login only; never automated',
             free_tier='University listing documents availability; owner entitlement/export licence unverified',
             documented_rate=None, enforced_rate='0logins,0queries,0exports', fields=[], pit_limitations='Current profile is not a historical certificate',
             lifecycle_limitations='Must supply dated class/listing and source/vintage evidence', licensing='No scrape, licence bypass or programmatic redistribution',
             authoritative_for='None without separately supplied dated evidence'),
        dict(common, name='CRSP methodology documentation', role='SECONDARY_CROSS_CHECK', authority='Methodology reference only; no CRSP market data',
             purpose='Ex-distribution-date adjustment factor definition referenced by Tiingo; indexed publisher definition motivates a separate consistency probe',
             documentation=['https://www.crsp.org/wp-content/uploads/guides/CRSP_Calculations_and_Index_Methodologies.pdf',
                            'https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/'],
             authentication='None for public documentation; no licensed database access', free_tier='Public documentation only; live links returned404, complete current guide not certified',
             documented_rate=None, enforced_rate='Bounded browser documentation review only;0CRSP data calls',
             fields=['Cash distribution/ex-date price factor definition'], pit_limitations='Publisher-indexed definition is not a contemporaneous Tiingo version certificate',
             lifecycle_limitations='No event amounts, identities, listing spans or terminal terms acquired from CRSP',
             licensing='No licensed market data downloaded/redistributed; reference attribution retained', authoritative_for='No pilot observation; interpretation remains provisional')]
    value = {'version': 'phase3c_source_registry_v001', 'as_of': '2026-10-12', 'sources': sources,
             'archived_documentation_receipts': json.loads((RAW/'documentation_summary.json').read_bytes())}
    validate_registry(value); return value


def validate_registry(value):
    rows = value['sources']
    if len({r['name'] for r in rows}) != len(rows): raise ValueError('Duplicate source registry entry')
    required = {'name', 'role', 'authority', 'purpose', 'documentation', 'review_date', 'authentication', 'free_tier',
                'documented_rate', 'enforced_rate', 'fields', 'pit_limitations', 'lifecycle_limitations', 'licensing', 'authoritative_for'}
    for r in rows:
        if not required.issubset(r) or r['role'] not in ('PRIMARY_SOURCE', 'SECONDARY_CROSS_CHECK'):
            raise ValueError('Incomplete source registry/authority classification')
        if not r['documentation'] or not all(u.startswith('https://') for u in r['documentation']):
            raise ValueError('Official documentation missing')
