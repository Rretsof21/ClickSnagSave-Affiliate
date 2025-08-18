import argparse, os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.utils import Env, DATA_DIR, TEMPLATES_DIR

def load_products():
    return Env.read_json(os.path.join(DATA_DIR,'products_latest.json'))

def render_cards(products):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(['html']))
    tpl = env.get_template('site_card.html.jinja')
    return "\n".join([tpl.render(product=p) for p in products])

def inject_into_index(site_dir, cards_html, tzname, disclosure):
    index_path = os.path.join(site_dir, 'index.html')
    with open(index_path,'r',encoding='utf-8') as f:
        html = f.read()
    stamp = Env.now_local(tzname).strftime('%Y-%m-%d %H:%M %Z')
    marker = '<!-- DEALS_INJECT -->'
    block = f"\n<section class=\"deals\">\n<p class=\"disclosure\">{disclosure}</p>\n<p class=\"stamp\">Prices and availability are accurate as of {stamp} and subject to change.</p>\n<ul class=\"grid\">{cards_html}</ul>\n</section>\n"
    if marker in html:
        html = html.split(marker)[0] + marker + block + html.split(marker)[1]
    else:
        html = html.replace('</body>', block + '\n</body>')
    with open(index_path,'w',encoding='utf-8') as f:
        f.write(html)

def git_add_commit_push(branch):
    os.system('git add -A'); os.system('git commit -m "chore: update deals" || echo "no changes"'); os.system(f'git push origin {branch}')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); args = ap.parse_args()
    cfg = Env.load_config(args.config)
    products = load_products()
    cards_html = render_cards(products)
    inject_into_index(cfg['github']['site_dir'], cards_html, cfg['app']['timezone'], cfg['legal']['disclosure'])
    git_add_commit_push(cfg['github']['branch'])

if __name__ == '__main__':
    main()
