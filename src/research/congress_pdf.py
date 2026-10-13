"""Offline original-PDF projection; pypdf is isolated, never a source transport."""
def main():
    import argparse,json,hashlib
    from pathlib import Path
    from pypdf import PdfReader
    import importlib.metadata
    p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();body=Path(a.path).read_bytes()
    if not body.startswith(b'%PDF'):raise ValueError('Not an original PDF')
    reader=PdfReader(a.path)
    result={'source_sha256':hashlib.sha256(body).hexdigest(),'parser':'pypdf','parser_version':importlib.metadata.version('pypdf'),
        'pages':[{'page':i,'text':page.extract_text(extraction_mode='layout') or ''} for i,page in enumerate(reader.pages)],
        'network':False,'PDF_scripts_executed':False,'text_empty_does_not_prove_no_trades':True}
    print(json.dumps(result,ensure_ascii=True))

if __name__=='__main__':main()
