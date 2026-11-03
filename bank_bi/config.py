from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
MARKER = 'bank-marketing-intelligence:v1'


def database_kwargs():
    return dict(host=os.getenv('PGHOST', '127.0.0.1'),
                port=int(os.getenv('PGPORT', '5432')),
                dbname=os.getenv('PGDATABASE', 'bank_marketing_intelligence'),
                user=os.getenv('PGUSER', 'bank_bi'), password=os.environ['PGPASSWORD'])


def save(name, value):
    import json
    (ROOT / 'artifacts').mkdir(exist_ok=True)
    (ROOT / 'artifacts' / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')
