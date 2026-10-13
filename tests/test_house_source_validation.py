import unittest,hashlib,json
from src.research.house_source_validation import house_population,parse_ocr_rows,compare,evaluate_gate
from src.research.congress_originals import select_original_row
from src.research.house_ocr import CONFIG

def token(text,x,y,width=50):
    return {'text':text,'box':[[x,y],[x+width,y],[x+width,y+12],[x,y+12]],'confidence':0.99}

class HouseValidationTests(unittest.TestCase):
    def test_senate_outside_scope_and_unknown_chamber_not_house(self):
        self.assertEqual(house_population([{'chamber':'house'},{'chamber':'senate'},{}]),[{'chamber':'house'}])
    def test_ocr_extracts_source_row_without_expected_values(self):
        p={'source_sha256':'a'*64,'pages':[{'page':2,'width':800,'height':600,'render_sha256':'b'*64,
            'tokens':[token('Issuer Common (ABC)',10,100,190),token('S',210,100,10),token('02/03/2020',260,100,90)]}]}
        rows=parse_ocr_rows(p);self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['action'],'sale');self.assertEqual(rows[0]['transaction_date'],'2020-02-03')
        self.assertEqual(rows[0]['source_locator']['source_sha256'],'a'*64)
        self.assertEqual(rows[0]['source_locator']['render_sha256'],'b'*64)
        self.assertEqual(rows[0]['source_locator']['page'],2)
    def test_source_action_date_disagreement_not_hidden_by_association(self):
        expected={'trade_key':['house','D',0],'asset_description':'Issuer Common','printed_ticker':'ABC','action':'purchase','transaction_date':'2020-01-01'}
        row={'asset_text':'Issuer Common (ABC)','action':'sale','transaction_date':'2020-02-03'}
        result=compare(expected,select_original_row(expected,[row]))
        self.assertEqual(result['transaction_type'],'DISAGREE');self.assertEqual(result['transaction_date'],'DISAGREE')
        self.assertEqual(result['asset_description'],'AGREE');self.assertEqual(result['printed_ticker'],'AGREE')
    def test_ocr_unknown_is_not_zero_or_sale(self):
        self.assertEqual(compare({},None)['transaction_type'],'UNKNOWN')
        self.assertEqual(parse_ocr_rows({'pages':[{'tokens':[],'page':0,'width':800}]}),[])
    def test_resolver_symbol_not_original_comparison(self):
        result=compare({'asset_description':'Issuer','printed_ticker':'OLD','resolved_ticker':'NEW','action':'purchase','transaction_date':'2020-01-01'},
                       {'asset_text':'Issuer (OLD)','action':'purchase','transaction_date':'2020-01-01'})
        self.assertEqual(result['printed_ticker'],'AGREE')
    def test_asset_normalization_ignores_spacing_punctuation_only(self):
        r={'asset_description':'Issuer, Inc.','action':'sale','transaction_date':'2020-01-01'}
        a={'asset_text':'ISSUER INC','action':'sale','transaction_date':'2020-01-01'}
        self.assertEqual(compare(r,a)['asset_description'],'AGREE')
        a['asset_text']='Different Inc';self.assertEqual(compare(r,a)['asset_description'],'UNKNOWN')
    def test_gate_requires_55_and_retains_unknowns(self):
        c={'source_gate':{'denominator':61,'minimum_decisive':55,'decisive_date_agreement_min':.98,'decisive_type_agreement_min':.98,'decisive_asset_agreement_min':.95}}
        r={'fields':{'transaction_type':'AGREE','transaction_date':'AGREE','asset_description':'AGREE'},'action_expected':'purchase','actual_action':'purchase','year':'2014','printed_present':False,'amendment':False}
        unknown=dict(r,fields={k:'UNKNOWN' for k in r['fields']},actual_action=None)
        gate=evaluate_gate([r]*54+[unknown]*7,c);self.assertEqual(gate['verdict'],'ABANDON_EXP007_SOURCE_FEASIBILITY')
        self.assertEqual(gate['unknown'],7)
    def test_nonpurchase_extracted_as_purchase_also_fails(self):
        c={'source_gate':{'denominator':61,'minimum_decisive':55,'decisive_date_agreement_min':.98,'decisive_type_agreement_min':.98,'decisive_asset_agreement_min':.95}}
        r={'fields':{'transaction_type':'AGREE','transaction_date':'AGREE','asset_description':'AGREE'},'action_expected':'sale','actual_action':'purchase','year':'2015','printed_present':True,'amendment':False}
        self.assertFalse(evaluate_gate([r]*61,c)['checks']['no_purchase_disagreement'])
    def test_configuration_has_no_expected_fields(self):
        self.assertNotIn('expected',CONFIG);self.assertEqual(CONFIG['CPU_threads'],1)
    def test_repeated_asset_cannot_use_uncertified_ocr_ordinal(self):
        from src.research.house_source_validation import associate_ocr_row
        expected={'asset_description':'Issuer','trade_key':['house','D',0]}
        rows=[{'asset_text':'Issuer','action':'sale'},{'asset_text':'Issuer','action':'purchase'}]
        self.assertIsNone(associate_ocr_row(expected,rows))
    def test_worker_rejects_new_original_or_expected_field(self):
        from src.research.house_ocr import validate_dispatch
        self.assertTrue(validate_dispatch({'documents':[{'path':'original.pdf','sha256':'A'}]},['A']))
        with self.assertRaises(ValueError):validate_dispatch({'documents':[{'path':'original.pdf','sha256':'B'}]},['A'])
        with self.assertRaises(ValueError):validate_dispatch({'documents':[{'path':'original.pdf','sha256':'A','expected_action':'purchase'}]},['A'])
    def test_render_and_text_tampering_rejected(self):
        import tempfile
        from pathlib import Path
        from src.research.house_repair_report import verify_projection
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'page_000.png').write_bytes(b'image')
            p={'evidence_tier':'DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL','network_disabled':True,'pages':[
                {'render_path':'page_000.png','render_sha256':hashlib.sha256(b'image').hexdigest(),'text':'source','text_sha256':hashlib.sha256(b'source').hexdigest()}]}
            self.assertTrue(verify_projection(p,folder));p['pages'][0]['text']='altered'
            with self.assertRaises(ValueError):verify_projection(p,folder)
            p['pages'][0]['render_path']='../escape.png'
            with self.assertRaises(ValueError):verify_projection(p,folder)
    def test_checkbox_columns_extract_action_without_expected_action(self):
        page={'page':0,'width':900,'height':600,'render_sha256':'b'*64,'tokens':[
            token('Purchase',250,40),token('Sale',320,40),token('Exchange',390,40),
            token('Issuer Inc',30,100,140),token('×',335,100,10),token('01/02/2020',460,100,80),token('01/03/2020',570,100,80)]}
        r=parse_ocr_rows({'source_sha256':'a'*64,'pages':[page]})
        self.assertEqual(len(r),1);self.assertEqual(r[0]['action'],'sale');self.assertEqual(r[0]['transaction_date'],'2020-01-02')
    def test_source_bitmap_checkbox_requires_one_unambiguous_cell(self):
        page={'page':0,'width':900,'height':600,'render_sha256':'b'*64,'tokens':[
            token('Purchase',250,40),token('Sale',320,40),token('Exchange',390,40),
            token('Issuer Inc',30,100,140),token('01/02/2020',460,100,80)]}
        class Crop:
            def __init__(self,marked):self.marked=marked
            def convert(self,mode):return self
            def getdata(self):return [0]*10+[255]*90 if self.marked else [255]*100
        class Image:
            def crop(self,bounds):return Crop(bounds[0]<280)
        rows=parse_ocr_rows({'source_sha256':'a'*64,'pages':[page]},lambda *_:Image())
        self.assertEqual(rows[0]['action'],'purchase')
        self.assertIn('purchase',rows[0]['source_bitmap_checkbox_cells'])
    def test_repeated_core_equivalence_does_not_select_expected_date(self):
        from src.research.house_source_validation import associate_ocr_row
        expected={'asset_description':'Issuer','transaction_date':'2030-01-01','action':'sale'}
        row={'asset_text':'Issuer','action':'purchase','transaction_date':'2020-01-01','source_locator':{'page':0},'minimum_confidence':.9}
        actual=associate_ocr_row(expected,[row,dict(row,source_locator={'page':1})])
        self.assertEqual(compare(expected,actual)['transaction_date'],'DISAGREE')
        self.assertEqual(len(actual['source_locator']['equivalent_candidate_locators']),2)

