# checks/check_disponibility.py

import asyncio
import checks.check_admin as check_admin
import checks.check_nodes as check_nodes
import checks.check_sessions as check_sessions
import checks.check_matriz as check_matriz
import checks.check_etrader as check_etrader
import checks.check_webService as check_webService
import checks.check_accountReport as check_accountReport
import logging

# Configuración básica de logging (opcional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_check():
    checks = {
        "admin": check_admin.run_check(),
        "nodes": check_nodes.run_check(),
        "sessions": check_sessions.run_check(),
        "matriz": check_matriz.run_check(),
        "etrader": check_etrader.run_check(),
        "webService": check_webService.run_check(),
        "accountReport": check_accountReport.run_check(),
    }

    logger.info("Iniciando ejecución paralela de chequeos de disponibilidad...")

    results = await asyncio.gather(*checks.values(), return_exceptions=True)

    response = {}
    for name, result in zip(checks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Error en el check '{name}': {str(result)}")
            response[name] = {"error": str(result)}
        else:
            response[name] = result

    logger.info("Finalizó ejecución de todos los chequeos.")
    return response
