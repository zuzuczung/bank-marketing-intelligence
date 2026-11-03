"""Download only the official UCI archive; verify the pinned CSV before loading."""
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
import requests
from .config import ROOT, save

URL = 'https://archive.ics.uci.edu/static/public/222/bank+marketing.zip'
PAGE = 'https://archive.ics.uci.edu/dataset/222/bank+marketing'
COLUMNS = ['age','job','marital','education','default','balance','housing','loan',
           'contact','day','month','duration','campaign','pdays','previous','poutcome','y']
MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def download():
    folder = ROOT / 'data/raw'
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / 'bank-full.csv'
    manifest_path = ROOT / 'source-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if not dest.exists():
        r = requests.get(URL, timeout=90)
        r.raise_for_status()
        outer = zipfile.ZipFile(io.BytesIO(r.content))
        if 'bank.zip' in outer.namelist():
            bank = zipfile.ZipFile(io.BytesIO(outer.read('bank.zip')))
        else:
            bank = outer
        data = bank.read('bank-full.csv')
        if manifest and digest(data) != manifest['csv_sha256']:
            raise RuntimeError('Source checksum changed; review before replacing the pinned source')
        dest.write_bytes(data)
        (folder / 'bank-names.txt').write_bytes(bank.read('bank-names.txt'))
        if not manifest:
            manifest = dict(source_page=PAGE, download_url=URL, file='bank-full.csv',
                            archive_sha256=digest(r.content), csv_sha256=digest(data),
                            received_at=datetime.now(timezone.utc).isoformat(),
                            license='CC BY 4.0', doi='10.24432/C5K306', expected_rows=45211)
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    if not manifest or digest(dest.read_bytes()) != manifest['csv_sha256']:
        raise RuntimeError('Local source checksum does not match the source manifest')
    return dest


def rows():
    path = download()
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        if reader.fieldnames != COLUMNS:
            raise ValueError('Unexpected CSV schema')
        return list(reader)


def profile(data):
    p = dict(rows=len(data), subscribers=sum(r['y']=='yes' for r in data),
             contacts=sum(int(r['campaign']) for r in data),
             exact_duplicate_excess=len(data)-len({tuple(r[c] for c in COLUMNS) for r in data}),
             blank_cells={c:sum(not r[c].strip() for r in data) for c in COLUMNS},
             unknown_counts={c:sum(r[c]=='unknown' for r in data) for c in COLUMNS},
             ranges={c:dict(min=min(int(r[c]) for r in data),max=max(int(r[c]) for r in data))
                     for c in ['age','balance','day','duration','campaign','pdays','previous']},
             outcomes=dict(Counter(r['y'] for r in data)))
    save('source-profile.json',p)
    return p
