import argparse, os, time, csv, requests, datetime
from src.utils import Env, DATA_DIR

BASE = "https://api.canva.com"

def oauth_token(client_id, client_secret, refresh_token):
    r = requests.post(f"{BASE}/rest/v1/oauth/token",
        headers={"Content-Type":"application/x-www-form-urlencoded"},
        data={
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
        },
        timeout=60)
    r.raise_for_status()
    return r.json()['access_token']

def create_design_from_template(token, template_id):
    # Duplicate 9-slide template without touching master
    r = requests.post(f"{BASE}/v1/designs",
        headers={"Authorization": f"Bearer {token}"},
        json={"templateId": template_id},
        timeout=60)
    r.raise_for_status()
    return r.json()['id']

def set_variables_for_products(token, design_id, rows, cfg):
    # Slides 2–9 map to products 1–8; Slide 1 unchanged
    name_pat = cfg['canva'].get('name_field_pattern',"Product Name {i}")
    old_pat  = cfg['canva'].get('old_price_field_pattern',"Old Price {i}")
    new_pat  = cfg['canva'].get('new_price_field_pattern',"New Price {i}")
    pct_pat  = cfg['canva'].get('pct_field_pattern',"%{i}")
    variables = {}
    for idx, row in enumerate(rows[:8], start=1):
        variables[name_pat.format(i=idx)] = row['title']
        variables[old_pat.format(i=idx)]  = (f"${float(row['old_price']):.2f}" if row.get('old_price') else "")
        variables[new_pat.format(i=idx)]  = (f"${float(row['new_price']):.2f}" if row.get('new_price') else "")
        pct_val = ""
        if row.get('discount_percent'):
            try:
                pct_val = f"{int(float(row['discount_percent']))}% OFF"
            except:
                pct_val = f"{row['discount_percent']}% OFF"
        variables[pct_pat.format(i=idx)]  = pct_val

    r = requests.post(f"{BASE}/v1/designs/{design_id}/variables",
        headers={"Authorization": f"Bearer {token}"},
        json={"variables": variables},
        timeout=60)
    r.raise_for_status()

def export_all_pages(token, design_id, out_dir, size=1080):
    r = requests.post(f"{BASE}/v1/designs/{design_id}/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"format": "png", "size": {"width": size, "height": size}},
        timeout=60)
    r.raise_for_status()
    job = r.json()['id']
    for _ in range(80):
        s = requests.get(f"{BASE}/v1/exports/{job}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        s.raise_for_status()
        j = s.json()
        if j.get('status') == 'completed':
            files = []
            if isinstance(j.get('files'), list) and j['files']:
                files = j['files']
            elif j.get('url'):
                files = [{"url": j['url'], "page": 1}]
            if files:
                os.makedirs(out_dir, exist_ok=True)
                for i, f in enumerate(files, start=1):
                    img = requests.get(f['url'], timeout=60); img.raise_for_status()
                    with open(os.path.join(out_dir, f"slide_{i:02d}.png"), 'wb') as fp:
                        fp.write(img.content)
                return
        time.sleep(3)
    raise RuntimeError("Canva export timed out")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = Env.load_config(args.config)

    rows = list(csv.DictReader(open(os.path.join(DATA_DIR,'products_latest.csv'),'r',encoding='utf-8')))

    token = oauth_token(cfg['canva']['client_id'], cfg['canva']['client_secret'], cfg['canva']['refresh_token'])
    design_id = create_design_from_template(token, cfg['canva']['template_id'])
    set_variables_for_products(token, design_id, rows, cfg)

    today = datetime.datetime.now().strftime('%Y%m%d')
    out_dir = os.path.join(cfg['github']['ig_asset_dir'], f"daily_{today}")
    export_all_pages(token, design_id, out_dir, size=int(cfg['canva']['export_size']))

if __name__ == '__main__':
    main()
