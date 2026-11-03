import argparse
import json
from .config import ROOT,save


def main():
    parser=argparse.ArgumentParser(description='UCI Bank Marketing → Python/SQL → Superset')
    parser.add_argument('command',choices=['download','bootstrap','load','dashboard','verify','report','all'])
    args=parser.parse_args()
    if args.command in ['download','all']:
        from .source import download
        print('Source ready:',download().name)
    if args.command in ['bootstrap','all']:
        from .bootstrap import main as bootstrap
        bootstrap()
    if args.command in ['load','all']:
        from .pipeline import load
        load()
    if args.command in ['dashboard','all']:
        from .dashboard import main as dashboard
        dashboard()
    if args.command in ['verify','all']:
        from .pipeline import validate
        from .verify import main as verify
        validate();verify()
    if args.command in ['report','all']:
        from .report import main as report
        report()


if __name__=='__main__':main()
