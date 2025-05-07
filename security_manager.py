import json
import os
import base64
import logging
import binascii # Importe binascii para capturar erros de base64 inválido

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

def _obfuscate_token(token):
    """Obfuscação simples do token usando Base64."""
    if not token:
        return ""
    try:
        encoded_bytes = base64.b64encode(token.encode('utf-8'))
        return encoded_bytes.decode('utf-8')
    except Exception as e:
        # Mantém o log existente para outros tipos de erro
        logger.error(f"Erro inesperado ao obfuscate o token: {e}", exc_info=True)
        return token # Retorna o token original em caso de erro (menos seguro, mas evita quebrar)

def _deobfuscate_token(obfuscated_token):
    """
    Deobfuscação simples do token usando Base64.
    Trata erros de decodificação para compatibilidade com arquivos antigos/inválidos.
    """
    if not obfuscated_token:
        return ""
    try:
        # Tenta decodificar de Base64 e depois para UTF-8
        decoded_bytes = base64.b64decode(obfuscated_token.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except (UnicodeDecodeError, binascii.Error) as e:
        # Captura erros específicos de decodificação (UTF-8 inválido ou Base64 inválido)
        logger.warning(f"Falha ao deobfuscate o token (formato inválido?): {e}. O token será usado como está (pode ser texto puro ou inválido).")
        return obfuscated_token # Retorna a string original que falhou na decodificação
    except Exception as e:
        # Captura outros erros inesperados durante a deobfuscação
        logger.error(f"Erro inesperado ao deobfuscate o token: {e}", exc_info=True)
        return obfuscated_token # Retorna a string original em caso de erro


# ... restante das funções load_configuration e save_configuration (mantêm-se as mesmas) ...
# Coloque as funções load_configuration e save_configuration após as funções _obfuscate_token e _deobfuscate_token
# para garantir que sejam encontradas.

def load_configuration():
    """
    Carrega as configurações de um arquivo JSON, deobfuscando o token.
    Retorna um dicionário com as configurações ou None em caso de erro/arquivo inexistente.
    """
    # Usa CONFIG_FILE definido neste módulo
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Arquivo de configuração {CONFIG_FILE} não encontrado.")
        return None

    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)

        # Deobfusca o token ao carregar usando a função modificada
        if "token" in config_data:
            config_data["token"] = _deobfuscate_token(config_data["token"])

        logger.info(f"Configurações carregadas de {CONFIG_FILE}.")
        return config_data

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar o arquivo de configurações {CONFIG_FILE}: {e}. Verifique o formato do arquivo.", exc_info=True)
        return None

    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado ao carregar configurações de {CONFIG_FILE}: {e}", exc_info=True)
        return None


def save_configuration(config_data):
    """
    Salva as configurações em um arquivo JSON, obfuscando o token.
    config_data deve ser um dicionário com as configurações.
    """
    config_data_to_save = config_data.copy() # Crie uma cópia para não modificar o dicionário original

    # Obfusca o token antes de salvar usando a função
    if "token" in config_data_to_save:
        config_data_to_save["token"] = _obfuscate_token(config_data_to_save["token"])

    # Usa CONFIG_FILE definido neste módulo
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data_to_save, f, indent=4)
        logger.info(f"Configurações salvas em {CONFIG_FILE}.")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configurações em {CONFIG_FILE}: {e}", exc_info=True)
        return False