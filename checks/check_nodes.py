import aiohttp
import asyncio
from datetime import datetime
import ssl
from supabase import create_client, Client
import os
from concurrent.futures import ThreadPoolExecutor

ssl_context = ssl.create_default_context()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta supabase_url"
assert SUPABASE_KEY is not None, "Falta supabase_key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_envs():
    response = supabase.table("instancias") \
        .select("env, url, name, token, sessions") \
        .eq("status", 1) \
        .execute()
    return response.data


def fetch_endpoints():
    response = supabase.table("url_checks") \
        .select("url") \
        .eq("type", "NODES") \
        .execute()
    return response.data


def log_to_db_sync(logs):
    payload = [{
        "check_name": check_name,
        "instance": instance,
        "date": date,
        "output": output,
        "error": error
    } for (check_name, instance, date, output, error) in logs]
    supabase.table("checks_logs").insert(payload).execute()


async def check_nodes_with_retry(session, env, base_url, endpoint_url, token, sessions, instance, retries=3, backoff_factor=0.5):
    nodes_url = f'https://api-risk.{env}.{base_url}.com.ar{endpoint_url}'
    headers = {'Authorization': f'Basic {token}'}
    timeout = 40 if instance == 'Inviu' else 10
    error_message = None

    for attempt in range(retries):
        try:
            async with session.get(nodes_url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    json_response = await response.json()
                    result = process_response(json_response, sessions)
                    return result, nodes_url
                else:
                    error_message = f"HTTP {response.status} - {response.reason}"
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            error_message = str(e)
        if attempt < retries - 1:
            await asyncio.sleep(backoff_factor * (2**attempt))

    if error_message and "Timeout" in error_message:
        return "Timeout luego de 3 intentos", nodes_url
    return error_message, nodes_url


def process_response(json_response, sessions):
    required_ids = [
        "risk-calculator-", "risk-", "fix-", "markets-connector-mtr-", "api-risk-"
    ]

    response_ids = [item['id'] for item in json_response['response']]

    missing_required_ids = [
        rid for rid in required_ids
        if not any(id.startswith(rid) for id in response_ids)
    ]

    if missing_required_ids:
        return f"Faltan nodos requeridos: {', '.join(missing_required_ids)}"

    if 'F' in sessions and not any(id.startswith("markets-connector-mfci-") for id in response_ids):
        return "Falta el nodo opcional: markets-connector-mfci-"

    if 'B' in sessions and not any(id.startswith("markets-connector-byma-") for id in response_ids):
        return "Falta el nodo opcional: markets-connector-byma-"

    return True


async def run_check():
    check_name = "Check Nodes"
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_logs = []

    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        env_rows = await loop.run_in_executor(executor, fetch_envs)
        endpoint_rows = await loop.run_in_executor(executor, fetch_endpoints)

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            tasks = []
            metadata = []

            for env in env_rows:
                env_code = env['env'].strip()
                base_url = env['url'].strip()
                token = env['token'].strip()
                sessions = env['sessions'].strip()
                instance = env['name'].strip()

                for endpoint in endpoint_rows:
                    url_path = endpoint['url'].strip()
                    tasks.append(
                        check_nodes_with_retry(session, env_code, base_url, url_path, token, sessions, instance)
                    )
                    metadata.append(instance)

            results = await asyncio.gather(*tasks)

            for (result, full_url), instance in zip(results, metadata):
                if result is True:
                    output = "Nodes OK"
                    error = 0
                elif result and "Timeout luego de 3 intentos" in result:
                    output = result
                    error = 0
                else:
                    output = f"Error en: {full_url} - Detalles: {result}"
                    error = 1

                all_logs.append((check_name, instance, date, output, error))

        await loop.run_in_executor(executor, log_to_db_sync, all_logs)

    return {"inserted_logs": len(all_logs), "status": "ok"}


# Solo para pruebas manuales
if __name__ == "__main__":
    asyncio.run(run_check())
