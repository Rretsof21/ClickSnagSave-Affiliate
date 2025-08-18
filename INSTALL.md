# Install & Run (Novice-Friendly)

## 0) Download & unzip
Unzip this folder into your repo (e.g., `rretsof21/ClickSnagSave-Affiliate`). Commit and push.

## 1) Add GitHub Actions secrets
Go to **Repo → Settings → Secrets and variables → Actions** and add:

- `ENV_YAML` → open `ENV_YAML_PREFILLED.txt` in this folder, copy all, paste here.
- `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY` (Product Advertising API keys)
- `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET`, `CANVA_REFRESH_TOKEN`, `CANVA_TEMPLATE_ID`
- `IG_USER_ID`, `FB_PAGE_ID`, `IG_LONG_LIVED_TOKEN`
- (Optional) `OPENAI_API_KEY`
- (Optional) `GH_TOKEN` (only if pushing to a different repo)

## 2) GitHub Pages (site)
If you use this repo’s `website/` folder, set:
- **Settings → Pages → Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/website`

`website/index.html` contains `<!-- DEALS_INJECT -->` where daily cards are inserted.

## 3) Canva template mapping (already set)
- Your template has **9 slides** total.
- Slide 1 (title) stays unchanged.
- Slides 2–9 fill from daily products 1–8 using these field names:
  - `Product Name i`
  - `Old Price i`
  - `New Price i`
  - `%{i}`
- If you change names later, update patterns in `.env.yml`:
  ```yaml
  canva:
    name_field_pattern: "Product Name {i}"
    old_price_field_pattern: "Old Price {i}"
    new_price_field_pattern: "New Price {i}"
    pct_field_pattern: "%{i}"
  ```

## 4) First run (dry run with sample CSV)
In **Actions**, run the workflow **manually**. Or locally:
```bash
pip install -r requirements.txt
echo "<paste your ENV_YAML here>" > .env.yml
python -m src.fetch_deals --config .env.yml --manual data/manual_feed_example.csv
python -m src.build_affiliate_links --config .env.yml
python -m src.canva_render --config .env.yml
python -m src.update_site --config .env.yml
python -m src.post_instagram --config .env.yml
```
This will export 9 PNGs to `website/assets/ig/daily_YYYYMMDD/` and post as a carousel.

## 5) Go live
Remove the `--manual` (the workflow already does). Ensure your Amazon Associates account is active and your keys are valid.
The workflow runs daily at **4:00 AM America/Chicago**.

## 6) Troubleshooting quick list
- **Fetch deals fails**: PA-API account not approved / wrong marketplace / throttled → try manual CSV.
- **Canva export fails**: refresh token invalid or missing scopes; re-do OAuth or confirm `design:content:read`, `design:content:write` scopes.
- **Site not updating**: ensure `website/index.html` has `<!-- DEALS_INJECT -->` and workflow has `contents: write` permission.
- **Instagram carousel fails**: check `IG_LONG_LIVED_TOKEN` (not expired), images exist in `website/assets/ig/daily_YYYYMMDD/` and are committed before post step.
