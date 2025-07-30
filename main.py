from flask import Flask, request, jsonify
import asyncio
import checks.check_admin as check_admin
import checks.check_nodes as check_nodes
import checks.check_sessions as check_sessions
import checks.check_matriz as check_matriz
import checks.check_etrader as check_etrader
import checks.check_webService as check_webService
import checks.check_accountReport as check_accountReport
import checks.check_disponibility as check_disponibility

app = Flask(__name__)


@app.route("/")
def home():
    return "Sistema de chequeos activo"


@app.route("/check-admin")
def trigger_check_admin():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_admin.run_check())
    return jsonify(result)


@app.route("/check-nodes")
def trigger_check_nodes():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_nodes.run_check())
    return jsonify(result)


@app.route("/check-sessions")
def trigger_check_sessions():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_sessions.run_check())
    return jsonify(result)


@app.route("/check-matriz")
def trigger_check_matriz():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_matriz.run_check())
    return jsonify(result)


@app.route("/check-etrader")
def trigger_check_etrader():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_etrader.run_check())
    return jsonify(result)


@app.route("/check-webService")
def trigger_check_webService():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_webService.run_check())
    return jsonify(result)


@app.route("/check-accountReport")
def trigger_check_accountReport():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_accountReport.run_check())
    return jsonify(result)


@app.route("/check-disponibility")
def trigger_check_disponibility():
    secret = request.args.get("secret")
    if secret != "mi-token-secreto":
        return jsonify({"error": "unauthorized"}), 403

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_disponibility.run_check())
    return jsonify(result)

#if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=8080, debug=True)
