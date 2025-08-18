# Minimal AWS Signature V4 signer for PA-API v5
import hashlib, hmac, datetime

def _sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def _getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = hmac.new(('AWS4' + key).encode('utf-8'), dateStamp.encode('utf-8'), hashlib.sha256).digest()
    kRegion = hmac.new(kDate, regionName.encode('utf-8'), hashlib.sha256).digest()
    kService = hmac.new(kRegion, serviceName.encode('utf-8'), hashlib.sha256).digest()
    kSigning = hmac.new(kService, b'aws4_request', hashlib.sha256).digest()
    return kSigning

def sign_paapi(host, region, target, body, access_key, secret_key):
    method = 'POST'
    service = 'ProductAdvertisingAPI'
    content_type = 'application/json; charset=UTF-8'
    amz_date = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    date_stamp = datetime.datetime.utcnow().strftime('%Y%m%d')

    canonical_uri = '/paapi5/' + ('getitems' if 'GetItems' in target else 'searchitems')
    canonical_querystring = ''
    canonical_headers = f'content-type:{content_type}\nhost:{host}\nx-amz-date:{amz_date}\nx-amz-target:{target}\n'
    signed_headers = 'content-type;host;x-amz-date;x-amz-target'

    payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    canonical_request = '\n'.join([method, canonical_uri, canonical_querystring, canonical_headers, signed_headers, payload_hash])

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
    string_to_sign = '\n'.join([algorithm, amz_date, credential_scope, hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()])

    kSigning = _getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(kSigning, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = f'{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
    return {
        'Content-Type': content_type,
        'X-Amz-Date': amz_date,
        'X-Amz-Target': target,
        'Authorization': authorization_header,
        'Host': host,
    }
