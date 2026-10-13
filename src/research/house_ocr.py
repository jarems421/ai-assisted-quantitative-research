"""One local, expected-value-blind OCR projection of the frozen House originals.

Run only in the isolated OCR interpreter. No source transport or market loader.
"""
import hashlib,json
from pathlib import Path

CONFIG={'render_scale':3.0,'det_limit_side_len':1536,'det_limit_type':'max',
        'text_score':0.5,'CPU_threads':1,'engine':'RapidOCR3.4.0_ONNX1.23.2',
        'scope':'All pages of frozen image-only transaction documents; no expected fields supplied'}


def sha(body):return hashlib.sha256(body).hexdigest()


def exclusive(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=body:raise ValueError('Immutable OCR conflict')
    else:
        with path.open('xb') as f:f.write(body)


def main():
    import argparse,importlib.metadata,io
    from unittest.mock import patch
    p=argparse.ArgumentParser();p.add_argument('dispatch');p.add_argument('output');a=p.parse_args()
    dispatch=json.loads(Path(a.dispatch).read_bytes());out=Path(a.output).resolve()
    if len(dispatch['documents'])>34:raise ValueError('OCR scope ceiling')
    with patch('socket.socket.connect',side_effect=ValueError('OCR network disabled')),patch('socket.create_connection',side_effect=ValueError('OCR network disabled')):
        import rapidocr,pypdfium2 as pdfium
        models=Path(rapidocr.__file__).parent/'models'
        model_hashes={x.name:sha(x.read_bytes()) for x in models.glob('*.onnx')}
        engine=rapidocr.RapidOCR(params={'Det.model_path':str(models/'ch_PP-OCRv4_det_infer.onnx'),
            'Rec.model_path':str(models/'ch_PP-OCRv4_rec_infer.onnx'),
            'Cls.model_path':str(models/'ch_ppocr_mobile_v2.0_cls_infer.onnx'),
            'Det.limit_side_len':CONFIG['det_limit_side_len'],'Det.limit_type':'max',
            'EngineConfig.onnxruntime.intra_op_num_threads':1,'EngineConfig.onnxruntime.inter_op_num_threads':1,
            'Global.text_score':0.5,'Global.log_level':'warning'})
        for d in dispatch['documents']:
            path=Path(d['path']);body=path.read_bytes()
            if sha(body)!=d['sha256']:raise ValueError('Original PDF hash mismatch')
            target=out/d['sha256']/'projection.json'
            if target.exists():
                old=json.loads(target.read_bytes())
                if old['source_sha256']!=d['sha256'] or old['configuration']!=CONFIG or old['model_hashes']!=model_hashes:raise ValueError('OCR cache mismatch')
                print('Verified OCR cache',flush=True);continue
            pdf=pdfium.PdfDocument(body);pages=[]
            for i in range(len(pdf)):
                page=pdf[i];bitmap=page.render(scale=CONFIG['render_scale']);im=bitmap.to_pil();buf=io.BytesIO();im.save(buf,format='PNG');render=buf.getvalue()
                render_path=target.parent/f'page_{i:03d}.png';exclusive(render_path,render)
                result=engine(im)
                tokens=[] if result.boxes is None else [{'box':box.tolist(),'text':text,'confidence':float(score)} for box,text,score in zip(result.boxes,result.txts,result.scores)]
                text='\n'.join(t['text'] for t in tokens)
                pages.append({'page':i,'width':im.width,'height':im.height,'render_path':render_path.name,'render_sha256':sha(render),
                    'tokens':tokens,'text':text,'text_sha256':sha(text.encode())})
                bitmap.close();page.close()
            pdf.close()
            record={'source_sha256':d['sha256'],'configuration':CONFIG,'model_hashes':model_hashes,
                'versions':{k:importlib.metadata.version(k) for k in ('rapidocr','onnxruntime','pypdfium2','pillow')},
                'evidence_tier':'DERIVED_PROJECTION_OF_PRIMARY_ORIGINAL','network_disabled':True,'pages':pages}
            exclusive(target,json.dumps(record,sort_keys=True,separators=(',',':')).encode())
            print('OCR complete:',len(pages),'pages',flush=True)


if __name__=='__main__':main()
