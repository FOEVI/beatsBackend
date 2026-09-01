from rest_framework_simplejwt.backends import TokenBackend

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjogOTk5OSwgInJvbGUiOiAiQWRtaW4ifQ.fakesignature"

backend = TokenBackend(algorithm="HS256", signing_key=None)

try:
    payload = backend.decode(token, verify=False)
    print("SUCCES -- payload decode :", payload)
except Exception as e:
    print("ECHEC -- type d'exception :", type(e).__name__)
    print("ECHEC -- message :", e)