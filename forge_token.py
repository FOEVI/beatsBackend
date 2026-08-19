import base64, json

def make_token(payload):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesignature"

print("=== Token 'utilisateur normal' (pas de role) ===")
print(make_token({"user_id": 9999}))
print()
print("=== Token FORGE avec role Admin ===")
print(make_token({"user_id": 9999, "role": "Admin"}))