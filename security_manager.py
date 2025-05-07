# security_manager.py
import json
import os
import base64
import logging
import binascii

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
        logger.error(f"Erro inesperado ao obfuscate o token: {e}", exc_info=True)
        return token

def _deobfuscate_token(obfuscated_token):
    """
    Deobfuscação simples do token usando Base64.
    Trata erros de decodificação para compatibilidade com arquivos antigos/inválidos.
    """
    if not obfuscated_token:
        return ""
    try:
        decoded_bytes = base64.b64decode(obfuscated_token.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except (UnicodeDecodeError, binascii.Error) as e:
         logger.warning(f"Erro ao decodificar token Base64: {e}. Token pode ser inválido ou não foi codificado em Base64. Retornando token original.", exc_info=True)
         return obfuscated_token
    except Exception as e:
        logger.error(f"Erro inesperado ao deobfuscate o token: {e}", exc_info=True)
        return obfuscated_token


def load_configuration():
    """
    Carrega as configurações de um arquivo JSON, deobfuscando o token e incluindo as opções de metadado.
    Retorna um dicionário com as configurações ou None se o arquivo não for encontrado ou houver erro.
    """
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Arquivo de configurações não encontrado: {CONFIG_FILE}")
        return None

    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)

        if "token" in config_data:
            config_data["token"] = _deobfuscate_token(config_data["token"])

        # --- Carregar as novas opções de metadado ---
        # Usa .get(key, default_value) para compatibilidade com arquivos antigos
        config_data["download_metadata_with_recording"] = config_data.get("download_metadata_with_recording", True) # Default é True
        config_data["download_metadata_without_recording"] = config_data.get("download_metadata_without_recording", True) # Default é True
        # --- Fim do carregamento das novas opções ---

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
    Salva as configurações em um arquivo JSON, obfuscando o token e incluindo as opções de metadado.
    config_data deve ser um dicionário com as configurações.
    Retorna True em sucesso, False em falha.
    """
    config_data_to_save = config_data.copy()

    if "token" in config_data_to_save:
        config_data_to_save["token"] = _obfuscate_token(config_data_to_save["token"])

    # As opções 'download_metadata_with_recording' e 'download_metadata_without_recording' já devem estar no dicionário passado pela GUI

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data_to_save, f, indent=4)

        logger.info(f"Configurações salvas em {CONFIG_FILE}.")
        return True

    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado ao salvar configurações em {CONFIG_FILE}: {e}", exc_info=True)
        return False