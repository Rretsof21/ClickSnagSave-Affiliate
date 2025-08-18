# Canva Setup (No Localhost)

## 1) Create Integration (Public → Draft)
- Name: any (e.g., ClickSnagSave Automation)
- Website: your GitHub Pages URL
- Authorized Redirect URL: `https://example.com`
- Scopes (minimum): `design:content:read`, `design:content:write`
- Copy **Client ID**, **Generate Client Secret**.

## 2) Get Authorization Code (PKCE S256)
Use this authorize link format (replace CLIENT_ID). Use the PKCE pair you generated.
```
https://www.canva.com/api/oauth/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=https%3A%2F%2Fexample.com&scope=design%3Acontent%3Aread%20design%3Acontent%3Awrite&state=abc123&code_challenge=YOUR_CODE_CHALLENGE&code_challenge_method=S256
```

After Allow, copy the `code=` value from the address bar.

## 3) Exchange code → refresh token
POST to `https://api.canva.com/rest/v1/oauth/token` with Basic Auth (client_id:client_secret). Body:
- `grant_type=authorization_code`
- `code=PASTE_CODE_HERE`
- `redirect_uri=https://example.com`
- `code_verifier=YOUR_CODE_VERIFIER`

The response has `"refresh_token"`. Save it in Actions secret `CANVA_REFRESH_TOKEN`.

## 4) Template ID
Copy the ID after `/design/` from your Canva template URL, save as `CANVA_TEMPLATE_ID`.
