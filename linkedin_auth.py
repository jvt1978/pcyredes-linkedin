import os
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")
SCOPES = "openid profile w_member_social"

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1>Autenticacion completada. Puedes cerrar esta ventana.</h1>")

    def log_message(self, format, *args):
        pass

def get_auth_url() -> str:
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "pcyredes_linkedin_bot"
    })
    return f"https://www.linkedin.com/oauth/v2/authorization?{params}"

def exchange_code_for_token(code: str) -> dict:
    response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
    )
    response.raise_for_status()
    return response.json()

def save_token(token_data: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def authenticate():
    global auth_code
    auth_code = None

    url = get_auth_url()
    print(f"\nAbriendo navegador para autenticacion con LinkedIn...")
    print(f"Si no se abre, ve a: {url}\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8000), CallbackHandler)
    print("Esperando callback de LinkedIn...")
    while auth_code is None:
        server.handle_request()

    print("Codigo recibido. Obteniendo token...")
    token_data = exchange_code_for_token(auth_code)
    save_token(token_data)
    print("Token guardado en token.json")
    return token_data["access_token"]

def get_access_token() -> str:
    # En Railway usamos la env var directamente
    env_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if env_token:
        return env_token
    token = load_token()
    if token:
        return token["access_token"]
    return authenticate()
