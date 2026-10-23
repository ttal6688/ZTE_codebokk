"""Losslessly package the full scan without committing large raw CSV files."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def package(out):
    entries=[]
    sources=sorted((out/'cases').glob('case_*/dual_stream_trials.csv'))+sorted((out/'cases').glob('case_*/single_dual_pairs.csv'))+[out/'single_dual_pairs.csv']
    for source in sources:
        target=source.with_suffix('.csv.gz')
        with source.open('rb') as src,target.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9) as dst:shutil.copyfileobj(src,dst)
        h=hashlib.sha256()
        with gzip.open(target,'rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        original=sha(source);assert original==h.hexdigest() and target.stat().st_size<100*1024**2
        entries.append(dict(csv=str(source.relative_to(out)).replace('\\','/'),gzip=str(target.relative_to(out)).replace('\\','/'),
                            raw_bytes=source.stat().st_size,gzip_bytes=target.stat().st_size,raw_sha256=original,gzip_sha256=sha(target),round_trip=True))
    (out/'compression_manifest.json').write_text(json.dumps(dict(status='passed',format='gzip, lossless, integer bitstrings preserved',files=entries),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(status='passed',files=len(entries),raw_bytes=sum(x['raw_bytes'] for x in entries),gzip_bytes=sum(x['gzip_bytes'] for x in entries))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results');a=p.parse_args();package(ROOT/a.results)
