from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os
import asyncio
from functools import wraps

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
ALLOWED_DOMAINS = ["primary.com.ar"]  # <-- Reemplazá esto por tu dominio real

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave-super-secreta")
app.config['SESSION_TYPE'] = 'filesystem'
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
@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url.replace("/login", "") + "/auth/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
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
        return "Error al obtener información del usuario", 400

    email = userinfo_response.json()["email"]
    domain = email.split("@")[-1]

    if domain not in ALLOWED_DOMAINS:
        return "Acceso denegado", 403

    session["email"] = email
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# --- Rutas principales ---
@app.route("/")
def home():
    if "email" in session:
        return f"Sesión activa como {session['email']} | <a href='/logout'>Logout</a>"
    else:
        return "<a href='/login'>Login con Google</a>"


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
