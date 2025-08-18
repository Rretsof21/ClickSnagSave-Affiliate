import argparse, csv, os, json
from typing import List, Dict, Any
import requests
from tenacity import retry, wait_exponential, stop_after_attempt
from src.utils import Env, DATA_DIR
from src.schemas import Product, Price
from src.aws_v4 import sign_paapi

SEARCH_ENDPOINT = "https://{host}/paapi5/searchitems"

RESOURCES = [
    "Images.Primary.Large",
    "ItemInfo.Title",
    "Offers.Listings.Price",
    "Offers.Listings.SavingBasis",
    "Offers.Listings.Promotions",
    "Offers.Summaries.LowestPrice",
]

@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
def paapi_call(url: str, target: str, payload: Dict[str, Any], host: str, region: str, access_key: str, secret_key: str):
    body = json.dumps(payload, separators=(',',':'))
    headers = sign_paapi(host, region, target, body, access_key, secret_key)
    r = requests.post(url, headers=headers, data=body, timeout=30)
    if r.status_code >= 400:
        raise requests.HTTPError(f"{r.status_code} {r.text}")
    return r.json()

def compute_discount(item: Dict[str, Any]):
    price = basis = None
    listings = (item.get('Offers') or {}).get('Listings') or []
    if listings:
        lst = listings[0]
        price = ((lst.get('Price') or {}).get('Amount'))
        basis = ((lst.get('SavingBasis') or {}).get('Amount'))
        if not basis:
            promo = lst.get('Promotions') or []
            if promo and promo[0].get('DiscountPercent'):
                d = promo[0]['DiscountPercent']
                if price and d and d < 100:
                    basis = price / (1 - d/100.0)
    pct = 0
    if price and basis and basis > price:
        pct = int(round((basis - price) / basis * 100))
    return price, basis, pct

def to_product(item: Dict[str, Any]) -> Product:
    asin = item.get('ASIN')
    title = (((item.get('ItemInfo') or {}).get('Title') or {}).get('DisplayValue')) or asin
    image = (((item.get('Images') or {}).get('Primary') or {}).get('Large') or {}).get('URL', '')
    product_url = f"https://www.amazon.com/dp/{asin}"
    price, basis, pct = compute_discount(item)
    return Product(
        asin=asin, title=title, image=image, product_url=product_url,
        pricing=Price(price=price, saving_basis=basis),
        discount_percent=pct
    )

def write_csv(products: List[Product], path: str):
    cols = ["asin","title","image_url","old_price","new_price","discount_percent","product_url"]
    with open(path,'w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for p in products:
            w.writerow({
                'asin': p.asin,
                'title': p.title,
                'image_url': p.image,
                'old_price': f"{p.pricing.saving_basis:.2f}" if p.pricing.saving_basis else '',
                'new_price': f"{p.pricing.price:.2f}" if p.pricing.price else '',
                'discount_percent': p.discount_percent,
                'product_url': p.product_url,
            })

def read_manual_csv(path: str) -> List[Product]:
    out = []
    with open(path,'r',encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            out.append(Product(
                asin=row['asin'],
                title=row['title'],
                image=row['image_url'],
                product_url=row['product_url'],
                pricing=Price(
                    price=float(row['new_price']) if row.get('new_price') else None,
                    saving_basis=float(row['old_price']) if row.get('old_price') else None,
                ),
                discount_percent=int(row['discount_percent']) if row.get('discount_percent') else 0,
            ))
    return out

def fetch_paapi(cfg) -> List[Product]:
    amazon = cfg['amazon']; app = cfg['app']
    host = amazon['host']; region = amazon['region']
    access_key = amazon['access_key']; secret_key = amazon['secret_key']; partner_tag = amazon['partner_tag']
    if not (access_key and secret_key and partner_tag):
        raise SystemExit("Missing Amazon PA-API credentials.")
    url = SEARCH_ENDPOINT.format(host=host)
    products: List[Product] = []
    for page in (1,2,3):
        payload = {
            "Keywords": "deal",
            "ItemPage": page,
            "ItemCount": 10,
            "PartnerType": "Associates",
            "PartnerTag": partner_tag,
            "Resources": RESOURCES,
            "SearchIndex": app.get("search_index","All")
        }
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
        try:
            resp = paapi_call(url, target, payload, host, region, access_key, secret_key)
        except Exception as e:
            if page == 1: raise
            else: break
        items = ((resp.get('SearchResult') or {}).get('Items')) or []
        for it in items:
            products.append(to_product(it))
    # de-dupe by ASIN
    seen = set(); uniq = []
    for p in products:
        if p.asin and p.asin not in seen:
            seen.add(p.asin); uniq.append(p)
    return uniq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--manual', help='Path to manual CSV fallback', default='')
    args = ap.parse_args()
    cfg = Env.load_config(args.config); app = cfg['app']
    products = read_manual_csv(args.manual) if args.manual else fetch_paapi(cfg)
    products = [p for p in products if p.discount_percent >= app['min_discount_percent']]
    products.sort(key=lambda p: p.discount_percent, reverse=True)
    products = products[: app['max_products']]
    j = [p.__dict__ | { 'pricing': p.pricing.__dict__ } for p in products]
    Env.write_json(j, os.path.join(DATA_DIR,'products_latest.json'))
    write_csv(products, os.path.join(DATA_DIR,'products_latest.csv'))

if __name__ == '__main__':
    main()
