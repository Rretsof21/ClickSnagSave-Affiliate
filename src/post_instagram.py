import argparse, os, glob, requests, re
from jinja2 import Environment, FileSystemLoader
from src.utils import Env

RAW_BASE = "https://raw.githubusercontent.com/"

def raw_url(owner_repo, branch, path):
    return f"{RAW_BASE}{owner_repo}/{branch}/{path}"

def publish_carousel(ig_user_id, access_token, image_urls, caption):
    # Create child containers
    children = []
    for url in image_urls:
        r = requests.post(f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
            data={'image_url': url, 'is_carousel_item': 'true', 'access_token': access_token}, timeout=60)
        r.raise_for_status()
        children.append(r.json()['id'])
    # Create the carousel container
    r2 = requests.post(f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
        data={'caption': caption, 'children': ','.join(children), 'media_type':'CAROUSEL', 'access_token': access_token}, timeout=60)
    r2.raise_for_status()
    container_id = r2.json()['id']
    # Publish
    p = requests.post(f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish",
        data={'creation_id': container_id, 'access_token': access_token}, timeout=60)
    p.raise_for_status()
    return p.json()

def render_caption(cfg, products):
    env = Environment(loader=FileSystemLoader('templates')); tpl = env.get_template('instagram_caption.txt.jinja')
    from datetime import datetime; now = datetime.now().strftime('%Y-%m-%d')
    return tpl.render(products=products, disclosure=cfg['legal']['disclosure'], now=now)

def natural_sort_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); args = ap.parse_args()
    cfg = Env.load_config(args.config); gh = cfg['github']; ig = cfg['instagram']
    # Today's folder
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    img_dir = os.path.join(gh['ig_asset_dir'], f"daily_{today}")
    files = sorted(glob.glob(os.path.join(img_dir, 'slide_*.png')), key=natural_sort_key)
    assert len(files) >= 9, f"Expected 9 slides, found {len(files)} in {img_dir}"
    raw_urls = [raw_url(gh['repo'], gh['branch'], os.path.relpath(p).replace('\\','/')) for p in files[:9]]
    products = Env.read_json('data/products_latest.json'); caption = render_caption(cfg, products)
    publish_carousel(ig['ig_user_id'], ig['access_token'], raw_urls, caption)

if __name__ == '__main__':
    main()
