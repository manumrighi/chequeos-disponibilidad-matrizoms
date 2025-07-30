from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_session import Session
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os
import asyncio
from functools import wraps

# Cargar variables de entorno desde .env para desarrollo local
# En producción (Render), las variables se configuran directamente en el servicio
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv no está instalado, continuamos sin él (útil en producción)
    pass

# Permitir HTTP en desarrollo local para OAuth (solo para desarrollo)
# En producción, esto se mantiene seguro (HTTPS)
import sys

def is_development():
    """Detecta si estamos en desarrollo local"""
    # Múltiples formas de detectar desarrollo local
    dev_indicators = [
        # Variables de entorno de desarrollo
        os.getenv('FLASK_ENV') == 'development',
        os.getenv('FLASK_DEBUG') == '1',
        # Si estamos ejecutando directamente con python app.py
        __name__ == "__main__",
        # Si el archivo app.py está en sys.argv (ejecución directa)
        any('app.py' in arg for arg in sys.argv),
        # Si no hay variables de producción típicas
        not os.getenv('RENDER_SERVICE_NAME'),  # Render
        not os.getenv('HEROKU_APP_NAME'),      # Heroku
    ]
    return any(dev_indicators)

# Solo en desarrollo local, permitir HTTP para OAuth
if is_development():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("🔧 Modo desarrollo: HTTP permitido para OAuth")

# --- Chequeos ---
import checks.check_admin as check_admin
import checks.check_nodes as check_nodes
import checks.check_sessions as check_sessions
import checks.check_matriz as check_matriz
import checks.check_etrader as check_etrader
import checks.check_webService as check_webService
import checks.check_accountReport as check_accountReport
import checks.check_disponibility as check_disponibility

# --- Configuración OAuth & Flask ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
ALLOWED_DOMAINS = ["primary.com.ar"]

app = Flask(__name__)
# Configurar rutas para templates y static en la nueva estructura
app.template_folder = 'templates'
app.static_folder = 'static'

app.secret_key = os.getenv("SECRET_KEY", "clave-super-secreta")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '../temp/flask_session'
Session(app)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


# --- Utilidades ---
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# --- Rutas Auth ---
@app.route("/login-page")
def login_page():
    if "email" in session:
        return redirect("/")
    return render_template("login.html")

@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Detectar si estamos en desarrollo local
    is_local_dev = request.host.startswith(('localhost', '127.0.0.1')) or 'ngrok' in request.host
    
    if is_local_dev:
        # Para desarrollo local, usar una URL base fija
        if 'ngrok' in request.host:
            redirect_uri = f"https://{request.host}/auth/callback"
        else:
            redirect_uri = "http://localhost:8080/auth/callback"
    else:
        # Para producción, usar la URL base actual
        redirect_uri = request.base_url.replace("/login", "") + "/auth/callback"

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Detectar si estamos en desarrollo local para el callback también
    is_local_dev = request.host.startswith(('localhost', '127.0.0.1')) or 'ngrok' in request.host
    
    if is_local_dev:
        if 'ngrok' in request.host:
            redirect_url = f"https://{request.host}/auth/callback"
        else:
            redirect_url = "http://localhost:8080/auth/callback"
    else:
        redirect_url = request.base_url

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=redirect_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.status_code != 200:
        return render_template("error.html", 
                             error_title="Error de Autenticación",
                             error_message="No se pudo obtener la información del usuario de Google.",
                             error_code=userinfo_response.status_code,
                             show_login=True), 400

    email = userinfo_response.json()["email"]
    domain = email.split("@")[-1]

    if domain not in ALLOWED_DOMAINS:
        return render_template("error.html",
                             error_title="Acceso Denegado", 
                             error_message=f"Tu dominio de email ({domain}) no está autorizado para acceder a este sistema. Solo usuarios con dominios corporativos autorizados pueden ingresar.",
                             error_code=403,
                             show_login=True), 403

    session["email"] = email
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# --- Rutas principales ---
@app.route("/")
def index():
    if "email" in session:
        return redirect("/home")
    else:
        return render_template("login.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/checks")
@login_required
def checks():
    return render_template("checks.html")


# --- Rutas protegidas con login_required ---
@app.route("/check-admin")
@login_required
def trigger_check_admin():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_admin.run_check())
    return jsonify(result)


@app.route("/check-nodes")
@login_required
def trigger_check_nodes():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_nodes.run_check())
    return jsonify(result)


@app.route("/check-sessions")
@login_required
def trigger_check_sessions():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_sessions.run_check())
    return jsonify(result)


@app.route("/check-matriz")
@login_required
def trigger_check_matriz():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_matriz.run_check())
    return jsonify(result)


@app.route("/check-etrader")
@login_required
def trigger_check_etrader():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_etrader.run_check())
    return jsonify(result)


@app.route("/check-webService")
@login_required
def trigger_check_webService():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_webService.run_check())
    return jsonify(result)


@app.route("/check-accountReport")
@login_required
def trigger_check_accountReport():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_accountReport.run_check())
    return jsonify(result)


@app.route("/check-disponibility")
@login_required
def trigger_check_disponibility():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_disponibility.run_check())
    return jsonify(result)


# --- Para ejecutar local si hiciera falta ---
if __name__ == "__main__":
     app.run(host="0.0.0.0", port=8080, debug=True) 