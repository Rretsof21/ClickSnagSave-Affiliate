import os, json, yaml
from datetime import datetime
from dateutil import tz

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, 'data')
TEMPLATES_DIR = os.path.join(ROOT, 'templates')

os.makedirs(DATA_DIR, exist_ok=True)

class Env:
    @staticmethod
    def load_config(path: str):
        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        def expand(val):
            if isinstance(val, str) and val.startswith('${{ secrets.'):
                key = val.split('${{ secrets.')[-1].split(' }}')[0].rstrip(' }')
                return os.environ.get(key, '')
            return val
        for sect in cfg:
            if isinstance(cfg[sect], dict):
                for k,v in cfg[sect].items():
                    cfg[sect][k] = expand(v)
        return cfg

    @staticmethod
    def now_local(tzname: str):
        tzinfo = tz.gettz(tzname)
        return datetime.now(tzinfo)

    @staticmethod
    def write_json(obj, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    @staticmethod
    def read_json(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
