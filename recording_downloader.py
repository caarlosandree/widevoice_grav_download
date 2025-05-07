# recording_downloader.py
import requests
import os
import datetime
import config
import time
import logging
import threading

from exceptions import DownloadCancelledError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5


def gerar_arquivo_metadado(chamada, caminho_arquivo_gravacao, status_callback=None):
    """
    Gera um arquivo TXT com os metadados da chamada.
    Salva no mesmo diretório da gravação ou com um nome indicando falha.
    """
    try:
        base, _ = os.path.splitext(caminho_arquivo_gravacao)
        caminho_arquivo_metadado = base + ".txt"

        metadata_content = "--- Metadados da Chamada ---\n"
        for key, value in chamada.items():
            metadata_content += f"{key.replace('_', ' ').capitalize()}: {value}\n"

        with open(caminho_arquivo_metadado, 'w', encoding='utf-8') as f:
            f.write(metadata_content)

        mensagem = f"Arquivo de metadado gerado: {os.path.basename(caminho_arquivo_metadado)}"
        if status_callback:
            status_callback(mensagem)
        logger.info(mensagem)

    except Exception as e:
        chamada_id = chamada.get('id', 'desconhecido')
        mensagem_erro = f"Erro ao gerar arquivo de metadado para Chamada ID {chamada_id}: {e}"
        if status_callback:
            status_callback(f"Erro: Falha ao gerar metadado para ID {chamada_id}.", level=logging.ERROR)
        logger.error(mensagem_erro, exc_info=True)


# Adicionar download_metadata_with_recording e download_metadata_without_recording como parâmetros
def baixar_gravacao(url_base, chamada, diretorio_base=None, status_callback=None, cancel_event=None,
                    download_metadata_with_recording=True, download_metadata_without_recording=True): # --- NOVOS PARAMS ---
    """
    Baixa um arquivo de gravação para o diretório local com tentativas e suporte a cancelamento.
    Gera metadado opcionalmente para chamadas sem gravação ou em caso de falha.
    diretorio_base: O diretório base para salvar as gravações.
    status_callback: Função opcional para reportar o status na GUI.
    cancel_event: Um threading.Event para sinalizar o cancelamento.
    download_metadata_with_recording: Booleano para baixar metadados com gravação (default True). # --- NOVO ---
    download_metadata_without_recording: Booleano para baixar metadados sem gravação (default True). # --- NOVO ---
    Retorna True em sucesso, False em falha, levanta DownloadCancelledError se cancelado.
    """
    chamada_id = chamada.get('id', 'desconhecido')
    numero_chamada = chamada.get('numero', 'desconhecido')
    datahora_chamada = chamada.get('datahora', 'desconhecido')

    if cancel_event and cancel_event.is_set():
        logger.debug(f"Baixar gravação: Cancelamento detectado antes de processar Chamada ID {chamada_id}.")
        raise DownloadCancelledError(f"Processamento cancelado para Chamada ID {chamada_id}.")


    # Verifica se a chamada possui o campo 'gravacao'
    if 'gravacao' not in chamada or not chamada['gravacao']:
        mensagem = f"Chamada: Número {numero_chamada} em {datahora_chamada} (ID {chamada_id}) - Não possui gravação."
        # --- Verifica a opção de metadado SEM gravação antes de processar ---
        if download_metadata_without_recording:
             mensagem += " Gerando apenas metadado em pasta separada."
             if status_callback:
                  status_callback(mensagem, level=logging.INFO)
             logger.info(f"recording_downloader: {mensagem}")

             # Tenta gerar o metadado apenas se a opção estiver habilitada
             try:
                 datahora_str = chamada.get('datahora', '')
                 ano, mes_str, dia_str = "0000", "00", "00"
                 hora_min_seg = "000000"

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
                           logger.warning(f"recording_downloader: Campo 'datahora' vazio para Chamada ID {chamada_id}. Usando data padrão para metadado sem gravação.")

                 except (ValueError, TypeError):
                      logger.warning(f"recording_downloader: Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00) para metadado sem gravação.")

                 diretorio_raiz = diretorio_base if diretorio_base else config.DIRETORIO_BASE_GRAVACOES

                 diretorio_base_metadado = os.path.join(diretorio_raiz, "Metadata_Only")
                 diretorio_destino_dia = os.path.join(diretorio_base_metadado, ano, mes_str, dia_str)

                 os.makedirs(diretorio_destino_dia, exist_ok=True)

                 nome_arquivo_base = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}"
                 caminho_arquivo_metadado_sem_gravacao = os.path.join(diretorio_destino_dia, f"{nome_arquivo_base}_METADADO_SEM_GRAVACAO.txt")

                 if cancel_event and cancel_event.is_set():
                     logger.debug(f"Baixar gravação: Cancelamento detectado antes de gerar metadado para Chamada ID {chamada_id}.")
                     raise DownloadCancelledError(f"Geração de metadado cancelada para Chamada ID {chamada_id} (sem gravação).")

                 gerar_arquivo_metadado(chamada, caminho_arquivo_metadado_sem_gravacao, status_callback)

             except DownloadCancelledError:
                 raise

             except Exception as e:
                 mensagem_erro_metadado = f"recording_downloader: Erro inesperado ao tentar gerar metadado para Chamada ID {chamada_id} sem gravação: {e}"
                 if status_callback:
                     status_callback(f"Erro: Falha ao gerar metadado para ID {chamada_id} (sem gravação).", level=logging.ERROR)
                 logger.error(mensagem_erro_metadado, exc_info=True)
                 return False

             return True # Consideramos processado mesmo sem gravação, se o metadado foi gerado com sucesso

        else:
             # --- Caso a opção de metadado SEM gravação não esteja habilitada e não tenha gravação ---
             mensagem += " Processamento ignorado conforme opção (sem gravação)."
             if status_callback:
                  status_callback(mensagem, level=logging.DEBUG)
             logger.debug(f"recording_downloader: {mensagem}")
             return True # Considerado processado/ignorado com sucesso


    # --- Continua a lógica de download APENAS SE HOUVER GRAVAÇÃO ---
    caminho_gravacao_api = chamada['gravacao'].replace("\\/", "/")
    url_gravacao = f"https://{url_base}/gravador28/{caminho_gravacao_api}.gsm"


    datahora_str = chamada.get('datahora', '')
    ano, mes_str, dia_str = "0000", "00", "00"
    hora_min_seg = "000000"

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
             logger.warning(f"recording_downloader: Campo 'datahora' vazio para Chamada ID {chamada_id}. Usando data padrão.")

    except (ValueError, TypeError) as e:
        mensagem = f"Aviso: Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00)."
        if status_callback:
            status_callback(mensagem, level=logging.WARNING)
        logger.warning(mensagem)

    diretorio_raiz = diretorio_base if diretorio_base else config.DIRETORIO_BASE_GRAVACOES
    diretorio_destino = os.path.join(diretorio_raiz, ano, mes_str, dia_str)


    try:
        os.makedirs(diretorio_destino, exist_ok=True)
    except Exception as e:
        logger.error(f"recording_downloader: Erro ao criar diretórios para Chamada ID {chamada_id} (Dir: {diretorio_destino}): {e}", exc_info=True)
        if status_callback:
            status_callback(f"Erro: Não foi possível criar diretórios para Chamada ID {chamada_id}.", level=logging.ERROR)
        # --- Tenta gerar metadado de erro APENAS SE A OPÇÃO DE METADADO COM GRAVAÇÃO ESTIVER HABILITADA ---
        if download_metadata_with_recording:
             try:
                  nome_arquivo_base = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}"
                  caminho_arquivo_metadado_erro_dir = os.path.join(diretorio_base if diretorio_base else ".", f"{nome_arquivo_base}_ERROR_DIR.txt")
                  gerar_arquivo_metadado(chamada, caminho_arquivo_metadado_erro_dir, status_callback)
             except Exception as meta_e:
                  logger.error(f"recording_downloader: Erro adicional ao gerar metadato de erro de diretório para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
        else:
            logger.debug(f"recording_downloader: Geração de metadado de erro de diretório para Chamada ID {chamada_id} ignorada conforme opção.")
        # --- FIM DA VERIFICAÇÃO DA OPÇÃO ---
        return False


    nome_arquivo = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}.gsm"
    caminho_arquivo_local = os.path.join(diretorio_destino, nome_arquivo)


    # --- Lógica de Tentativas de Download ---
    for attempt in range(MAX_RETRIES + 1):
        try:
            if cancel_event and cancel_event.is_set():
                logger.debug(f"Baixar gravação: Cancelamento detectado na tentativa {attempt} para Chamada ID {chamada_id}.")
                raise DownloadCancelledError(f"Processo de download cancelado para Chamada ID {chamada_id}.")

            if attempt > 0:
                mensagem_tentativa = f"Tentativa {attempt}/{MAX_RETRIES} de baixar: {url_gravacao} (Chamada ID {chamada_id}). Aguardando {RETRY_DELAY * attempt}s..."
                if status_callback:
                    status_callback(mensagem_tentativa)
                logger.info(mensagem_tentativa)
                time.sleep(RETRY_DELAY * attempt)

            else:
                 mensagem_tentativa_inicial = f"Tentando baixar gravação da chamada {chamada_id}: {url_gravacao}"
                 if status_callback:
                      status_callback(mensagem_tentativa_inicial)
                 logger.info(mensagem_tentativa_inicial)

            response_gravacao = requests.get(url_gravacao, stream=True, timeout=30)
            response_gravacao.raise_for_status()

            with open(caminho_arquivo_local, 'wb') as f:
                for chunk in response_gravacao.iter_content(chunk_size=8192):
                    if cancel_event and cancel_event.is_set():
                        logger.debug(f"Baixar gravação: Cancelamento detectado durante o download de Chamada ID {chamada_id}. Limpando arquivo parcial.")
                        raise DownloadCancelledError(f"Download cancelado durante a transferência para Chamada ID {chamada_id}.")
                    f.write(chunk)

            mensagem_sucesso = f"Download bem-sucedido: {nome_arquivo} (Chamada ID {chamada_id})."
            if status_callback:
                status_callback(mensagem_sucesso, level=logging.INFO)
            logger.info(mensagem_sucesso)

            if cancel_event and cancel_event.is_set():
                logger.debug(f"Baixar gravação: Cancelamento detectado antes de gerar metadado pós-download para Chamada ID {chamada_id}.")
                pass

            # --- Gerar metadado PÓS-DOWNLOAD APENAS SE A OPÇÃO DE METADADO COM GRAVAÇÃO ESTIVER HABILITADA ---
            if download_metadata_with_recording:
                 gerar_arquivo_metadado(chamada, caminho_arquivo_local, status_callback)
            else:
                 logger.debug(f"recording_downloader: Geração de metadado pós-download para Chamada ID {chamada_id} ignorada conforme opção.")
            # --- FIM DA VERIFICAÇÃO DA OPÇÃO ---

            return True

        except DownloadCancelledError:
            if os.path.exists(caminho_arquivo_local):
                 try:
                     os.remove(caminho_arquivo_local)
                     logger.debug(f"Baixar gravação: Arquivo parcial removido para Chamada ID {chamada_id} após cancelamento.")
                 except Exception as cleanup_e:
                     logger.error(f"recording_downloader: Erro ao limpar arquivo parcial {caminho_arquivo_local} após cancelamento: {cleanup_e}", exc_info=True)
            raise

        except requests.exceptions.HTTPError as e:
            mensagem_erro = f"Erro HTTP ({e.response.status_code} - {e.response.reason}) ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}). Não será retentado."
            if status_callback:
                status_callback(f"Erro HTTP {e.response.status_code} ao baixar gravação ID {chamada_id}.", level=logging.ERROR)
            logger.error(mensagem_erro, exc_info=True)
            # --- Tenta gerar metadado de falha APENAS SE A OPÇÃO DE METADADO COM GRAVAÇÃO ESTIVER HABILITADA ---
            if download_metadata_with_recording:
                 try:
                      gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_DOWNLOAD_FAILED.txt", status_callback)
                 except Exception as meta_e:
                      logger.error(f"recording_downloader: Erro adicional ao gerar metadato de falha para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
            else:
                 logger.debug(f"recording_downloader: Geração de metadado de falha para Chamada ID {chamada_id} ignorada conforme opção (erro HTTP).")
            # --- FIM DA VERIFICAÇÃO DA OPÇÃO ---
            return False

        except requests.exceptions.RequestException as e:
            mensagem_erro = f"Erro na requisição ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}): {e}"
            if status_callback:
                status_callback(f"Erro na requisição ao baixar gravação ID {chamada_id}.", level=logging.ERROR)
            logger.error(f"Erro na requisição de download para {url_gravacao}: {e}", exc_info=True)

            if attempt < MAX_RETRIES:
                pass
            else:
                mensagem_falha_final = f"Falha final ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}) após {MAX_RETRIES + 1} tentativas."
                if status_callback:
                    status_callback(f"Falha final ao baixar gravação ID {chamada_id}.", level=logging.ERROR)
                logger.error(mensagem_falha_final)
                # --- Tenta gerar metadado de falha APENAS SE A OPÇÃO DE METADADO COM GRAVAÇÃO ESTIVER HABILITADA ---
                if download_metadata_with_recording:
                     try:
                          gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_DOWNLOAD_FAILED.txt", status_callback)
                     except Exception as meta_e:
                          logger.error(f"recording_downloader: Erro adicional ao gerar metadato de falha final para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
                else:
                     logger.debug(f"recording_downloader: Geração de metadado de falha final para Chamada ID {chamada_id} ignorada conforme opção (falha na requisição).")
                # --- FIM DA VERIFICAÇÃO DA OPÇÃO ---
                return False

        except Exception as e:
            mensagem_erro_inesperado = f"Ocorreu um erro inesperado ao processar gravação da Chamada ID {chamada_id}: {e}"
            if status_callback:
                status_callback(f"Erro inesperado ao processar gravação ID {chamada_id}.", level=logging.ERROR)
            logger.exception(mensagem_erro_inesperado)
            # --- Tenta gerar metadado de erro inesperado APENAS SE A OPÇÃO DE METADADO COM GRAVAÇÃO ESTIVER HABILITADA ---
            if download_metadata_with_recording:
                 try:
                      gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_PROCESS_ERROR.txt", status_callback)
                 except Exception as meta_e:
                      logger.error(f"recording_downloader: Erro adicional ao gerar metadato de erro inesperado para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
            else:
                 logger.debug(f"recording_downloader: Geração de metadado de erro inesperado para Chamada ID {chamada_id} ignorada conforme opção.")
            # --- FIM DA VERIFICAÇÃO DA OPÇÃO ---
            return False

    logger.error(f"recording_downloader: Função baixar_gravacao terminou sem retornar para Chamada ID {chamada_id}. Considerado falha.")
    return False