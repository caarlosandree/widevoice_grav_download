import requests
import json
import logging
from datetime import datetime, timedelta

# Obtém um logger específico para este módulo
logger = logging.getLogger(__name__)

def construir_url_api(url_base, login, token):
    """Constrói a URL completa da API, removendo http/https se presentes na URL base."""
    url_base_limpa = url_base.replace("http://", "").replace("https://", "")
    return f"https://{url_base_limpa}/api.php?acao=statusreport&login={login}&token={token}"

def obter_dados_chamadas(url_api, datainicio_str, datafim_str, status_callback=None):
    """
    Faz a requisição para a API e retorna os dados das chamadas.
    status_callback é uma função opcional para reportar o status na GUI.
    """
    mensagem_inicio = f"\nConsultando a API em: {url_api}\nPeríodo: {datainicio_str} a {datafim_str}"
    if status_callback:
        status_callback(mensagem_inicio)
    logger.info(mensagem_inicio)

    payload = {
        "datainicio": datainicio_str,
        "datafim": datafim_str
    }

    try:
        response = requests.post(url_api, json=payload)
        response.raise_for_status()

        try:
            dados = response.json()
            logger.info("Dados da API obtidos com sucesso.")
            return dados
        except json.JSONDecodeError:
            mensagem_erro = "Erro ao decodificar a resposta JSON da API. A resposta pode não ser um JSON válido."
            if status_callback:
                status_callback(mensagem_erro)
            logger.error(mensagem_erro)
            return None

    except requests.exceptions.HTTPError as e:
        mensagem_erro = f"Erro HTTP na requisição da API: {e.response.status_code} - {e.response.reason}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Erro HTTP {e.response.status_code} ao consultar API: {e.response.reason}", exc_info=True)
        return None

    except requests.exceptions.ConnectionError as e:
        mensagem_erro = f"Erro de Conexão na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Erro de conexão ao consultar API: {e}", exc_info=True)
        return None

    except requests.exceptions.Timeout as e:
        mensagem_erro = f"Timeout na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Timeout ao consultar API: {e}", exc_info=True)
        return None

    except requests.exceptions.RequestException as e:
        mensagem_erro = f"Erro geral na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Erro geral na requisição da API: {e}", exc_info=True)
        return None

    except Exception as e:
        mensagem_erro = f"Ocorreu um erro inesperado ao obter dados da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.exception(f"Erro inesperado ao obter dados da API: {e}")
        return None

def obter_dados_completos(url_api, datainicio_str, datafim_str, status_callback=None):
    """
    Obtém todos os registros da API, respeitando o limite de 500 registros por requisição.
    Faz múltiplas chamadas incrementais com base na datahora.
    """
    todos_os_dados = []
    formato_datahora = "%Y-%m-%d %H:%M:%S"

    datainicio = datetime.strptime(datainicio_str, formato_datahora)
    datafim = datetime.strptime(datafim_str, formato_datahora)
    atual = datainicio

    while atual <= datafim:
        inicio_str = atual.strftime(formato_datahora)
        fim_str = datafim.strftime(formato_datahora)

        if status_callback:
            status_callback(f"Consultando: {inicio_str} até {fim_str}...")

        dados = obter_dados_chamadas(url_api, inicio_str, fim_str, status_callback)

        if not dados:
            break

        todos_os_dados.extend(dados)

        if len(dados) < 500:
            break

        try:
            ultima_datahora = max(
                datetime.strptime(chamada['datahora'], formato_datahora)
                for chamada in dados if 'datahora' in chamada
            )
        except (ValueError, KeyError):
            if status_callback:
                status_callback("Erro ao interpretar datahora dos registros.")
            logger.error("Erro ao interpretar datahora dos registros.")
            break

        atual = ultima_datahora + timedelta(seconds=1)

    if status_callback:
        status_callback(f"Total de registros obtidos: {len(todos_os_dados)}")
    logger.info(f"Total de registros obtidos: {len(todos_os_dados)}")

    return todos_os_dados