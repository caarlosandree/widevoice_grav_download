import requests
import os
import datetime
import config # Importa o módulo de configuração
import time # Importamos o módulo time para usar time.sleep
import logging # Importamos o módulo logging

# Obtém um logger específico para este módulo
logger = logging.getLogger(__name__)

# Parâmetros para tentativas de download
MAX_RETRIES = 3       # Número máximo de tentativas (além da primeira)
RETRY_DELAY = 5       # Atraso inicial entre as tentativas em segundos

# Adicionamos diretorio_base como um parâmetro opcional
def baixar_gravacao(url_base, chamada, diretorio_base=None, status_callback=None):
    """
    Baixa um arquivo de gravação para o diretório local com tentativas.
    diretorio_base: O diretório base para salvar as gravações (substitui o do config.py).
    status_callback é uma função opcional para reportar o status na GUI.
    As mensagens importantes também serão logadas.
    """
    caminho_gravacao_api = chamada['gravacao'].replace("\\/", "/")
    url_gravacao = f"https://{url_base}/gravador28/{caminho_gravacao_api}.gsm"
    chamada_id = chamada.get('id', 'desconhecido') # Obter ID mais cedo para usar nos logs/mensagens

    # Extrair data para estrutura de pastas e nome do arquivo
    datahora_str = chamada.get('datahora', '')
    data_chamada = None
    ano, mes_str, dia_str = "0000", "00", "00" # Valores padrão
    hora_min_seg = "000000" # Valor padrão para hora no nome do arquivo

    try:
        if datahora_str:
             data_chamada = datetime.datetime.strptime(datahora_str, '%Y-%m-%d %H:%M:%S')
             ano = str(data_chamada.year)
             mes = data_chamada.month
             dia = data_chamada.day
             mes_str = f"{mes:02d}"
             dia_str = f"{dia:02d}"
             hora_min_seg = data_chamada.strftime('%H%M%S')
        else:
             # Se datahora_str estiver vazio, levantamos um erro para usar o fallback de data
             raise ValueError("Campo 'datahora' vazio.")

    except (ValueError, TypeError) as e:
        mensagem = f"Aviso: Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00)."
        if status_callback:
            status_callback(mensagem)
        logger.warning(mensagem) # Loga aviso

    # Usar o diretório passado como parâmetro, se existir, senão usar o do config.py
    diretorio_raiz = diretorio_base if diretorio_base else config.DIRETORIO_BASE_GRAVACOES
    diretorio_destino = os.path.join(diretorio_raiz, ano, mes_str, dia_str)
    os.makedirs(diretorio_destino, exist_ok=True)

    numero_chamada = chamada.get('numero', 'desconhecido')

    # Formato do nome do arquivo: ANO_MES_DIA_NUMERO_HORAMINUTOSEGUNDO_ID.gsm
    nome_arquivo = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}.gsm"
    caminho_arquivo_local = os.path.join(diretorio_destino, nome_arquivo)

    # --- Lógica de Tentativas de Download ---
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                mensagem_tentativa = f"Tentativa {attempt}/{MAX_RETRIES} de baixar: {url_gravacao} (Chamada ID {chamada_id}). Aguardando {RETRY_DELAY * attempt}s..."
                if status_callback:
                    status_callback(mensagem_tentativa)
                logger.info(mensagem_tentativa) # Loga tentativa
                time.sleep(RETRY_DELAY * attempt) # Atraso exponencial

            else:
                 # Primeira tentativa
                 mensagem_tentativa_inicial = f"Tentando baixar gravação da chamada {chamada_id}: {url_gravacao}"
                 if status_callback:
                      status_callback(mensagem_tentativa_inicial)
                 logger.info(mensagem_tentativa_inicial) # Loga tentativa inicial


            response_gravacao = requests.get(url_gravacao, stream=True)
            response_gravacao.raise_for_status() # Lança exceção para status de erro (4xx, 5xx)

            # Se a requisição for bem-sucedida, escreve o arquivo
            with open(caminho_arquivo_local, 'wb') as f:
                for chunk in response_gravacao.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Se chegou aqui, o download foi bem-sucedido
            mensagem_sucesso = f"Download bem-sucedido: {nome_arquivo} (Chamada ID {chamada_id})."
            if status_callback:
                status_callback(mensagem_sucesso)
            logger.info(mensagem_sucesso) # Loga sucesso
            return True # Retorna True em caso de sucesso

        except requests.exceptions.HTTPError as e:
            mensagem_erro = f"Erro HTTP ({e.response.status_code} - {e.response.reason}) ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}). Não será retentado."
            if status_callback:
                status_callback(mensagem_erro)
            logger.error(mensagem_erro, exc_info=True) # Loga erro com traceback
            return False # Não tenta novamente para erros HTTP

        except requests.exceptions.RequestException as e:
            # Trata outros erros de requisição (conexão, timeout, etc.)
            mensagem_erro = f"Erro na requisição ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}): {e}"
            if status_callback:
                status_callback(mensagem_erro)
            logger.error(f"Erro na requisição de download para {url_gravacao}: {e}", exc_info=True) # Loga erro com traceback

            if attempt < MAX_RETRIES:
                # Continua para a próxima tentativa
                pass # O sleep já está no início do loop
            else:
                # Última tentativa falhou
                mensagem_falha_final = f"Falha final ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}) após {MAX_RETRIES + 1} tentativas."
                if status_callback:
                    status_callback(mensagem_falha_final)
                logger.error(mensagem_falha_final) # Loga falha final
                return False # Retorna False se todas as tentativas falharem

        except Exception as e:
            # Trata quaisquer outros erros inesperados durante o download/processamento
            mensagem_erro_inesperado = f"Ocorreu um erro inesperado ao processar gravação da Chamada ID {chamada_id}: {e}"
            if status_callback:
                status_callback(mensagem_erro_inesperado)
            logger.exception(mensagem_erro_inesperado) # Loga erro com traceback usando exception()
            return False # Erros inesperados geralmente não devem ser retentados

    # Se o loop terminar sem sucesso (improvável com o return False nos excepts, mas por garantia)
    logger.error(f"Função baixar_gravacao terminou sem retornar para Chamada ID {chamada_id}. Considerado falha.")
    return False