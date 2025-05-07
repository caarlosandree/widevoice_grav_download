# api_handler.py
import requests
import json
import logging
from datetime import datetime, timedelta
import threading

# Importar a exceção de cancelamento do novo arquivo exceptions.py
from exceptions import DownloadCancelledError # <--- MUDANÇA AQUI!

logger = logging.getLogger(__name__)

# ... (o restante das funções construir_url_api e obter_dados_chamadas permanecem o mesmo)
def construir_url_api(url_base, login, token):
    """Constrói a URL completa da API, removendo http/https se presentes na URL base."""
    url_base_limpa = url_base.replace("http://", "").replace("https://", "")
    return f"https://{url_base_limpa}/api.php?acao=statusreport&login={login}&token={token}"

def obter_dados_chamadas(url_api, datainicio_str, datafim_str, status_callback=None):
    """
    Faz a requisição para a API e retorna os dados das chamadas.
    status_callback é uma função opcional para reportar o status na GUI.
    """
    payload = {
        "datainicio": datainicio_str,
        "datafim": datafim_str
    }

    try:
        response = requests.post(url_api, json=payload, timeout=60)
        response.raise_for_status()

        try:
            dados = response.json()
            return dados
        except json.JSONDecodeError:
            mensagem_erro = "Erro ao decodificar a resposta JSON da API. A resposta pode não ser um JSON válido."
            if status_callback:
                status_callback(mensagem_erro, level=logging.ERROR)
            logger.error(mensagem_erro, exc_info=True)
            return None

    except requests.exceptions.HTTPError as e:
        mensagem_erro = f"Erro HTTP na requisição da API ({e.response.status_code} - {e.response.reason})."
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.error(f"Erro HTTP {e.response.status_code} ao consultar API: {e.response.reason}", exc_info=True)
        return None

    except requests.exceptions.ConnectionError as e:
        mensagem_erro = f"Erro de Conexão na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.error(f"Erro de conexão ao consultar API: {e}", exc_info=True)
        return None

    except requests.exceptions.Timeout as e:
        mensagem_erro = f"Timeout na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.error(f"Timeout ao consultar API: {e}", exc_info=True)
        return None

    except requests.exceptions.RequestException as e:
        mensagem_erro = f"Erro geral na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.error(f"Erro geral na requisição da API: {e}", exc_info=True)
        return None

    except Exception as e:
        mensagem_erro = f"Ocorreu um erro inesperado ao obter dados da API: {e}"
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.exception(f"Erro inesperado ao obter dados da API: {e}")
        return None


def obter_dados_completos(url_api, datainicio_str, datafim_str, status_callback=None, cancel_event=None):
    # ... (restante da função obter_dados_completos permanece o mesmo, apenas importa DownloadCancelledError do lugar certo)
    """
    Obtém todos os registros da API, respeitando o limite de 500 registros por requisição.
    Faz múltiplas chamadas incrementais com base na datahora.
    Aceita um evento de cancelamento.
    """
    todos_os_dados = []
    formato_datahora = "%Y-%m-%d %H:%M:%S"

    try:
        datainicio = datetime.strptime(datainicio_str, formato_datahora)
        datafim = datetime.strptime(datafim_str, formato_datahora)
    except ValueError:
        mensagem_erro = "Formato de data/hora inválido passado para obter_dados_completos."
        if status_callback:
            status_callback(mensagem_erro, level=logging.ERROR)
        logger.error(mensagem_erro)
        return None

    atual = datainicio

    mensagem_inicio_api = f"Consultando a API em: {url_api.split('?')[0]} para o período de {datainicio_str} a {datafim_str}"
    if status_callback:
         status_callback(mensagem_inicio_api)
    logger.info(mensagem_inicio_api)


    while atual <= datafim:
        if cancel_event and cancel_event.is_set():
            logger.debug("API Handler: Cancelamento detectado entre chamadas à API.")
            raise DownloadCancelledError("Processo cancelado pelo usuário durante a consulta à API.")

        inicio_str = atual.strftime(formato_datahora)
        fim_str = datafim.strftime(formato_datahora)

        if status_callback:
            status_callback(f"API: Consultando faixa: {inicio_str} até {fim_str}...")

        dados = obter_dados_chamadas(url_api, inicio_str, fim_str, status_callback)

        if dados is None:
            return None

        if not dados:
             logger.debug(f"API Handler: Nenhuns dados retornados para a faixa {inicio_str} a {fim_str}. Avançando 1 dia.")
             atual = atual + timedelta(days=1)
             continue

        todos_os_dados.extend(dados)

        if len(dados) < 500:
            break
        else:
            try:
                ultima_datahora = max(
                    datetime.strptime(chamada.get('datahora', '0000-00-00 00:00:00'), formato_datahora)
                    for chamada in dados
                )
                atual = ultima_datahora + timedelta(seconds=1)
                logger.debug(f"API Handler: Próxima faixa de consulta inicia em {atual.strftime(formato_datahora)}")

            except (ValueError, KeyError) as e:
                mensagem_erro = f"Erro ao interpretar datahora do último registro para determinar a próxima faixa: {e}. Abortando coleta."
                if status_callback:
                    status_callback(mensagem_erro, level=logging.ERROR)
                logger.error(mensagem_erro, exc_info=True)
                return None

    if cancel_event and cancel_event.is_set():
         logger.debug("API Handler: Cancelamento detectado após a coleta de dados.")
         pass

    if status_callback:
        status_callback(f"API: Coleta de dados finalizada. Total de registros obtidos: {len(todos_os_dados)}")
    logger.info(f"API Handler: Coleta de dados finalizada. Total de registros obtidos: {len(todos_os_dados)}")

    return todos_os_dados