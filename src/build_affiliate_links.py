import argparse, os
from urllib.parse import urlparse, urlunparse
from src.utils import Env, DATA_DIR

def with_tag(url: str, tag: str) -> str:
    u = urlparse(url)
    q = f"tag={tag}"
    if u.query:
        q = u.query + "&" + q
    return urlunparse((u.scheme, u.netloc, u.path, u.params, q, u.fragment))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = Env.load_config(args.config); tag = cfg['amazon']['partner_tag']
    items = Env.read_json(os.path.join(DATA_DIR,'products_latest.json'))
    for p in items:
        p['affiliate_url'] = with_tag(p['product_url'], tag)
    Env.write_json(items, os.path.join(DATA_DIR,'products_latest.json'))

if __name__ == '__main__':
    main()
