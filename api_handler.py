import requests
import json
import logging # Importamos o módulo logging

# Obtém um logger específico para este módulo
logger = logging.getLogger(__name__)

def construir_url_api(url_base, login, token):
    """Constrói a URL completa da API, removendo http/https se presentes na URL base."""
    # Limpa o início da URL se usuário incluir http ou https
    url_base_limpa = url_base.replace("http://", "").replace("https://", "")
    return f"https://{url_base_limpa}/api.php?acao=statusreport&login={login}&token={token}"

# Adicionamos status_callback como um parâmetro
def obter_dados_chamadas(url_api, datainicio_str, datafim_str, status_callback=None):
    """
    Faz a requisição para a API e retorna os dados das chamadas.
    status_callback é uma função opcional para reportar o status na GUI.
    As mensagens importantes também serão logadas.
    """
    mensagem_inicio = f"\nConsultando a API em: {url_api}\nPeríodo: {datainicio_str} a {datafim_str}"
    if status_callback:
        status_callback(mensagem_inicio)
    logger.info(mensagem_inicio) # Loga a mensagem de início

    payload = {
        "datainicio": datainicio_str,
        "datafim": datafim_str
    }

    try:
        response = requests.post(url_api, json=payload)
        response.raise_for_status() # Lança uma exceção para status de erro (4xx ou 5xx)

        # Tenta decodificar a resposta JSON
        try:
            dados = response.json()
            logger.info("Dados da API obtidos com sucesso.") # Loga sucesso
            return dados
        except json.JSONDecodeError:
             mensagem_erro = "Erro ao decodificar a resposta JSON da API. A resposta pode não ser um JSON válido."
             if status_callback:
                  status_callback(mensagem_erro)
             logger.error(mensagem_erro) # Loga erro
             return None

    except requests.exceptions.HTTPError as e:
        # Trata erros específicos de status HTTP (4xx, 5xx)
        mensagem_erro = f"Erro HTTP na requisição da API: {e.response.status_code} - {e.response.reason}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Erro HTTP {e.response.status_code} ao consultar API: {e.response.reason}", exc_info=True) # Loga erro com traceback
        return None

    except requests.exceptions.ConnectionError as e:
         # Trata erros de conexão (servidor inacessível, etc.)
         mensagem_erro = f"Erro de Conexão na requisição da API: {e}"
         if status_callback:
              status_callback(mensagem_erro)
         logger.error(f"Erro de conexão ao consultar API: {e}", exc_info=True) # Loga erro com traceback
         return None

    except requests.exceptions.Timeout as e:
         # Trata erros de timeout
         mensagem_erro = f"Timeout na requisição da API: {e}"
         if status_callback:
              status_callback(mensagem_erro)
         logger.error(f"Timeout ao consultar API: {e}", exc_info=True) # Loga erro com traceback
         return None

    except requests.exceptions.RequestException as e:
        # Trata outros erros gerais de requisição
        mensagem_erro = f"Erro geral na requisição da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.error(f"Erro geral na requisição da API: {e}", exc_info=True) # Loga erro com traceback
        return None

    except Exception as e:
        # Trata quaisquer outros erros inesperados
        mensagem_erro = f"Ocorreu um erro inesperado ao obter dados da API: {e}"
        if status_callback:
            status_callback(mensagem_erro)
        logger.exception(f"Erro inesperado ao obter dados da API: {e}") # Loga erro com traceback usando exception()
        return None