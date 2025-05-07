# download_controller.py
import logging
import threading
import concurrent.futures
import os
from datetime import datetime
import time

from api_handler import construir_url_api, obter_dados_completos
from recording_downloader import baixar_gravacao, gerar_arquivo_metadado
import config

from exceptions import DownloadCancelledError

logger = logging.getLogger(__name__)

MAX_WORKERS = 5

class DownloadController:
    def __init__(self, status_callback=None, progress_callback=None,
                 completion_callback=None, directory_getter=None,
                 progress_maximum_callback=None):
        """
        Inicializa o controlador de download.
        """
        self._status_callback = status_callback
        self._progress_callback = progress_callback
        self._completion_callback = completion_callback
        self._directory_getter = directory_getter
        self._progress_maximum_callback = progress_maximum_callback

        self._executor = None
        self._is_running = False
        self._cancel_event = None

        # --- Armazenar as opções de metadado passadas no start_download ---
        self._download_metadata_with_recording = True # Valor padrão
        self._download_metadata_without_recording = True # Valor padrão
        # --- Fim do armazenamento ---

        self._total_items_to_process = 0


    # Adicionar os dois parâmetros de metadado aqui
    def start_download(self, url_base, login, token, datainicio_str, datafim_str, cancel_event,
                         download_metadata_with_recording, download_metadata_without_recording): # --- NOVOS PARAMS ---
        """
        Inicia o processo de download em uma thread separada.

        Args:
            url_base, login, token, datainicio_str, datafim_str: Dados da GUI necessários para a API.
            cancel_event: Um threading.Event para sinalizar o cancelamento.
            download_metadata_with_recording: Booleano para baixar metadados com gravação. # --- NOVO ---
            download_metadata_without_recording: Booleano para baixar metadados sem gravação. # --- NOVO ---
        """
        if self._is_running:
            self._log_and_status("Aviso: O processo de download já está em execução.", level=logging.WARNING)
            return

        self._is_running = True
        self._cancel_event = cancel_event
        # --- Armazenar as opções de metadado passadas ---
        self._download_metadata_with_recording = download_metadata_with_recording
        self._download_metadata_without_recording = download_metadata_without_recording
        # --- Fim do armazenamento ---


        self._log_and_status("Controlador: Processo de download iniciado.")
        logger.info("DownloadController: Método start_download chamado.")

        diretorio_destino = self._get_download_directory()
        if not diretorio_destino:
            self._log_and_status("Erro: Diretório de destino não especificado.", level=logging.ERROR)
            logger.error("DownloadController: Diretório de destino não obtido.")
            self._process_completed()
            return

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)


        # Inicia a thread principal para orquestrar o download
        # Passa as opções de metadado para a tarefa principal
        process_thread = threading.Thread(
             target=self._process_download_task,
             args=(url_base, login, token, datainicio_str, datafim_str, diretorio_destino,
                   self._download_metadata_with_recording, self._download_metadata_without_recording) # --- PASSA AS OPÇÕES ---
         )
        process_thread.start()


    # Adicionar os dois parâmetros de metadado aqui
    def _process_download_task(self, url_base, login, token, datainicio_str, datafim_str, diretorio_destino,
                                download_metadata_with_recording, download_metadata_without_recording): # --- NOVOS PARAMS ---
        """
        Tarefa principal de download executada na thread separada.
        Coordena a obtenção de dados da API e o download/processamento das gravações em paralelo.
        Verifica o evento de cancelamento periodicamente.
        Recebe as opções de download de metadados.
        """
        logger.info("DownloadController: Thread de processamento principal iniciada.")
        total_chamadas = 0
        try:
            if self._cancel_event and self._cancel_event.is_set():
                 raise DownloadCancelledError("Processo cancelado pelo usuário durante a obtenção de dados da API.")

            self._log_and_status("Controlador: Obtendo lista de chamadas da API...")
            url_api = construir_url_api(url_base, login, token)
            dados_chamadas = obter_dados_completos(url_api, datainicio_str, datafim_str,
                                                    status_callback=self._log_and_status,
                                                    cancel_event=self._cancel_event)


            if self._cancel_event and self._cancel_event.is_set():
                 raise DownloadCancelledError("Processo cancelado pelo usuário após a obtenção de dados da API.")


            if dados_chamadas is None:
                self._log_and_status("Controlador: Falha ao obter dados da API. Verifique logs para mais detalhes.", level=logging.ERROR)
                logger.error("DownloadController: Falha ao obter dados da API.")
                self._update_progress(0, 0)
                return

            if not isinstance(dados_chamadas, list) or not dados_chamadas:
                self._log_and_status("Controlador: Nenhum registro encontrado ou resposta da API em formato inesperado.", level=logging.WARNING)
                logger.info("DownloadController: Nenhum registro encontrado ou resposta da API em formato inesperado.")
                self._total_items_to_process = 0
                self._update_progress_maximum(0)
                self._update_progress(0, 0)
                return

            total_chamadas = len(dados_chamadas)
            self._total_items_to_process = total_chamadas
            self._log_and_status(f"Controlador: Encontrados {total_chamadas} registros de chamadas para processar.")
            logger.info(f"DownloadController: Encontrados {total_chamadas} registros de chamadas.")

            self._update_progress_maximum(total_chamadas)
            self._update_progress(0, total_chamadas)

            processados_count = 0
            future_to_chamada = {}

            self._log_and_status("Controlador: Iniciando processamento paralelo de gravações e metadados...")

            if self._cancel_event and self._cancel_event.is_set():
                 raise DownloadCancelledError("Processo cancelado pelo usuário antes de submeter tarefas.")

            for chamada in dados_chamadas:
                 tem_gravacao = 'gravacao' in chamada and bool(chamada.get('gravacao'))

                 if tem_gravacao:
                      # Passa as duas opções de metadado para baixar_gravacao
                      future = self._executor.submit(
                          baixar_gravacao, url_base, chamada, diretorio_destino, self._log_and_status, self._cancel_event,
                          download_metadata_with_recording, download_metadata_without_recording # --- PASSA AS OPÇÕES ---
                      )
                      future_to_chamada[future] = (chamada, 'download')
                 else:
                      # Passa as duas opções de metadado para _processar_sem_gravacao
                      future = self._executor.submit(
                          self._processar_sem_gravacao, chamada, self._log_and_status, diretorio_destino, self._cancel_event,
                          download_metadata_with_recording, download_metadata_without_recording # --- PASSA AS OPÇÕES ---
                      )
                      future_to_chamada[future] = (chamada, 'metadado_sem_gravacao')


            self._log_and_status("Controlador: Aguardando conclusão das tarefas...")

            for future in concurrent.futures.as_completed(future_to_chamada):
                if self._cancel_event and self._cancel_event.is_set():
                    logger.info("Controlador: Evento de cancelamento detectado no loop as_completed.")

                processados_count += 1
                self._update_progress(processados_count, self._total_items_to_process)

                chamada_info = future_to_chamada[future]
                chamada_original = chamada_info[0]
                tipo_tarefa = chamada_info[1]
                chamada_id = chamada_original.get('id', 'desconhecido')

                try:
                    result = future.result()
                    if tipo_tarefa == 'download' and result is False:
                         logger.warning(f"DownloadController: Tarefa de download falhou para Chamada ID {chamada_id}.")
                    elif tipo_tarefa == 'metadado_sem_gravacao' and result is False:
                         logger.warning(f"DownloadController: Tarefa de gerar metadado para Chamada ID {chamada_id} (sem gravação) falhou.")

                except DownloadCancelledError:
                    logger.debug(f"Controlador: Tarefa para Chamada ID {chamada_id} relatou cancelamento.")

                except Exception as exc:
                    mensagem_erro = f"Controlador: Ocorreu uma exceção não tratada ao processar a chamada ID {chamada_id}: {exc}"
                    self._log_and_status(mensagem_erro, level=logging.ERROR)
                    logger.exception(f"DownloadController: Exceção não tratada ao processar chamada ID {chamada_id}")

            if self._cancel_event and self._cancel_event.is_set():
                 self._log_and_status("Controlador: Processo de download cancelado pelo usuário.", level=logging.WARNING)
                 logger.info("Controlador: Processo de download interrompido por cancelamento.")
                 self._update_progress(processados_count, self._total_items_to_process)

            else:
                 gravacoes_baixadas_count = 0
                 erros_download_count = 0
                 processados_sem_gravacao_count = 0
                 erros_metadado_sem_gravacao_count = 0
                 cancelled_count = 0

                 for future in future_to_chamada:
                      tipo_tarefa = future_to_chamada[future][1]
                      try:
                          result = future.result()
                          if result is True:
                              if tipo_tarefa == 'download': gravacoes_baixadas_count += 1
                              elif tipo_tarefa == 'metadado_sem_gravacao': processados_sem_gravacao_count += 1
                          elif result is False:
                              if tipo_tarefa == 'download': erros_download_count += 1
                              elif tipo_tarefa == 'metadado_sem_gravacao': erros_metadado_sem_gravacao_count += 1
                      except DownloadCancelledError:
                           cancelled_count += 1
                      except Exception:
                          if tipo_tarefa == 'download': erros_download_count += 1
                          elif tipo_tarefa == 'metadado_sem_gravacao': erros_metadado_sem_gravacao_count += 1


                 self._log_and_status("\n--- Resumo do Processo ---")
                 self._log_and_status(f"Controlador: Total de registros da API encontrados: {total_chamadas}")
                 self._log_and_status(f"Controlador: Total de registros processados (baixados ou metadado gerado): {processados_count}")
                 self._log_and_status(f"Controlador: Gravações baixadas com sucesso: {gravacoes_baixadas_count}")

                 # --- Ajustar o resumo para refletir as novas opções de metadado ---
                 if download_metadata_with_recording and download_metadata_without_recording:
                     self._log_and_status(f"Controlador: Registros sem gravação processados (metadado gerado): {processados_sem_gravacao_count}")
                 elif download_metadata_without_recording:
                     self._log_and_status(f"Controlador: Registros sem gravação processados (metadado gerado): {processados_sem_gravacao_count}")
                 elif download_metadata_with_recording:
                      self._log_and_status("Controlador: Geração de metadados para registros sem gravação foi ignorada conforme opção.")
                 else:
                      self._log_and_status("Controlador: Geração de metadados (com ou sem gravação) foi ignorada conforme opção.")

                 if download_metadata_with_recording and (erros_download_count > 0 or any(f.exception() for f in future_to_chamada if future_to_chamada[f][1] == 'download' and not isinstance(f.exception(), DownloadCancelledError))):
                      self._log_and_status("Controlador: Metadados de falha de download podem ter sido gerados.", level=logging.WARNING)

                 if download_metadata_without_recording and erros_metadado_sem_gravacao_count > 0:
                     self._log_and_status(f"Controlador: Erros ao processar registros sem gravação (geração de metadado): {erros_metadado_sem_gravacao_count}", level=logging.WARNING)
                     self._log_and_status("Controlador: Verifique as mensagens de error acima e os logs para detalhes.")


                 if cancelled_count > 0:
                      self._log_and_status(f"Controlador: Tarefas individuais canceladas: {cancelled_count}", level=logging.WARNING)


                 if erros_download_count == 0 and erros_metadado_sem_gravacao_count == 0 and cancelled_count == 0:
                      if download_metadata_with_recording or download_metadata_without_recording:
                           self._log_and_status("Controlador: Todos os registros aplicáveis foram processados sem erros ou cancelamentos.")
                      else:
                           self._log_and_status("Controlador: Todos os registros foram processados (download de gravação opcional, metadados ignorados).")
                      logger.info("Controlador: Processo finalizado com sucesso (sem erros ou cancelamentos nas tarefas aplicáveis).")
                 elif cancelled_count > 0 and erros_download_count == 0 and erros_metadado_sem_gravacao_count == 0:
                       self._log_and_status("Controlador: Processo finalizado com algumas tarefas canceladas, mas sem outros erros.", level=logging.WARNING)
                       logger.info("Controlador: Processo finalizado com algumas tarefas canceladas.")
                 else:
                      self._log_and_status("Controlador: Processo finalizado com erros ou cancelamentos.", level=logging.ERROR)
                      logger.error("Controlador: Processo finalizado com erros ou cancelamentos.")

                 # --- Fim do ajuste do resumo ---


                 self._update_progress(total_chamadas, total_chamadas)

        except DownloadCancelledError as e:
            self._log_and_status(f"Controlador: Processo de download cancelado: {e}", level=logging.WARNING)
            logger.info("Controlador: Processo de download interrompido por cancelamento.")

        except Exception as e:
            mensagem_erro_inesperado = f"Controlador: Ocorreu um erro inesperado durante o processamento principal: {e}"
            self._log_and_status(mensagem_erro_inesperado, level=logging.ERROR)
            logger.exception("Controlador: Erro inesperado durante o processamento principal.")

        finally:
            if self._executor:
                logger.info("Controlador: Desligando ThreadPoolExecutor.")
                self._executor.shutdown(wait=True)
                self._executor = None
            self._is_running = False
            self._cancel_event = None
            # --- Resetar as opções de metadado para padrão ao finalizar (opcional, mas seguro) ---
            self._download_metadata_with_recording = True
            self._download_metadata_without_recording = True
            # --- Fim do reset ---
            self._process_completed()


    # Adicionar os dois parâmetros de metadado aqui
    def _processar_sem_gravacao(self, chamada, status_callback, diretorio_raiz, cancel_event,
                                 download_metadata_with_recording, download_metadata_without_recording): # --- NOVOS PARAMS ---
        """
        Método auxiliar executado em threadpool para processar chamadas sem gravação.
        Gera apenas o metadado em uma subpasta separada, se a opção estiver habilitada.
        Retorna True em sucesso/ignorado, False em falha, levanta DownloadCancelledError se cancelado.
        Aceita o evento de cancelamento e as opções de metadado.
        """
        # --- Verifica a opção de metadado SEM gravação ANTES de processar ---
        if not download_metadata_without_recording:
             chamada_id = chamada.get('id', 'desconhecido')
             mensagem = f"Chamada: ID {chamada_id} - Não possui gravação. Geração de metadado ignorada conforme opção."
             if status_callback:
                 status_callback(mensagem, level=logging.DEBUG)
             logger.debug(f"Controlador._processar_sem_gravacao: {mensagem}")
             return True

        if cancel_event and cancel_event.is_set():
            logger.debug(f"Processar sem gravação: Cancelamento detectado para Chamada ID {chamada.get('id', 'desconhecido')}.")
            raise DownloadCancelledError(f"Processamento cancelado para Chamada ID {chamada.get('id', 'desconhecido')} (sem gravação).")

        chamada_id = chamada.get('id', 'desconhecido')
        numero_chamada = chamada.get('numero', 'desconhecido')
        datahora_chamada = chamada.get('datahora', 'desconhecido')

        datahora_str = datahora_chamada
        ano, mes_str, dia_str = "0000", "00", "00"
        hora_min_seg = "000000"

        try:
             if datahora_str:
                  data_chamada = datetime.strptime(datahora_str, '%Y-%m-%d %H:%M:%S')
                  ano = str(data_chamada.year)
                  mes_str = f"{data_chamada.month:02d}"
                  dia_str = f"{data_chamada.day:02d}"
                  hora_min_seg = data_chamada.strftime('%H%M%S')
             else:
                  logger.warning(f"Controlador._processar_sem_gravacao: Campo 'datahora' vazio ou inválido para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00) para metadado sem gravação.")

        except (ValueError, TypeError):
             logger.warning(f"Controlador._processar_sem_gravacao: Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00) para metadado sem gravação.")


        if not diretorio_raiz:
             diretorio_raiz = config.DIRETORIO_BASE_GRAVACOES
             logger.warning(f"Controlador._processar_sem_gravacao: Diretório raiz vazio para Chamada ID {chamada_id}. Usando diretório do config: {diretorio_raiz}")

        diretorio_base_metadado = os.path.join(diretorio_raiz, "Metadata_Only")
        diretorio_destino_dia = os.path.join(diretorio_base_metadado, ano, mes_str, dia_str)

        try:
             os.makedirs(diretorio_destino_dia, exist_ok=True)
        except Exception as e:
             logger.error(f"Controlador._processar_sem_gravacao: Erro ao criar diretórios para metadado sem gravação (ID {chamada_id}, Dir: {diretorio_destino_dia}): {e}", exc_info=True)
             if status_callback:
                 status_callback(f"Erro: Não foi possível criar diretórios para metadado ID {chamada_id}.", level=logging.ERROR)
             return False


        nome_arquivo_base = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}"
        caminho_arquivo_metadado_sem_gravacao = os.path.join(diretorio_destino_dia, f"{nome_arquivo_base}_METADADO_SEM_GRAVACAO.txt")

        try:
            mensagem = f"Chamada: Número {numero_chamada} em {datahora_chamada} (ID {chamada_id}) - Não possui gravação. Gerando apenas metadado em pasta separada."
            if status_callback:
                 status_callback(mensagem)
            logger.info(f"Controlador._processar_sem_gravacao: {mensagem}")

            # gerar_arquivo_metadado já verifica cancelamento internamente se o parâmetro for passado
            gerar_arquivo_metadado(chamada, caminho_arquivo_metadado_sem_gravacao, status_callback)
            return True

        except Exception as e:
            mensagem_erro_metadado = f"Controlador._processar_sem_gravacao: Erro inesperado ao tentar gerar metadado para Chamada ID {chamada_id} sem gravação: {e}"
            if status_callback:
                status_callback(f"Erro ao gerar metadado para Chamada ID {chamada_id}.", level=logging.ERROR)
            logger.error(mensagem_erro_metadado, exc_info=True)
            return False


    def _log_and_status(self, message, level=logging.INFO):
        if level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        elif level == logging.DEBUG:
             logger.debug(message)


        if self._status_callback:
            try:
                self._status_callback(message, level)
            except Exception as e:
                logger.error(f"Controlador: Erro ao chamar status_callback: {e} - Mensagem: {message}",
                             exc_info=True)

    def _update_progress(self, value, total=None):
        if self._progress_callback:
            try:
                self._progress_callback(value, total)
            except Exception as e:
                logger.error(f"Controlador: Erro ao chamar progress_callback: {e} - Valor: {value}, Total: {total}", exc_info=True)

    def _update_progress_maximum(self, maximum):
        """Chama o callback para definir o valor máximo para a barra de progresso."""
        if self._progress_maximum_callback:
            try:
                self._progress_maximum_callback(maximum)
                logger.debug(f"Controlador: Chamado progress_maximum_callback com {maximum}")
            except Exception as e:
                logger.error(f"Controlador: Erro ao chamar progress_maximum_callback: {e} - Máximo: {maximum}", exc_info=True)
        else:
             logger.debug(f"Controlador: progress_maximum_callback não configurado. Máximo: {maximum}")

    def _get_download_directory(self):
        if self._directory_getter:
            try:
                return self._directory_getter()
            except Exception as e:
                logger.error(f"Controlador: Erro ao chamar directory_getter: {e}", exc_info=True)
                return None
        logger.warning("Controlador: directory_getter não configurado.")
        return None

    def _process_completed(self):
        logger.info("Controlador: Processo de download concluído ( callback_called ).")
        if self._completion_callback:
            try:
                self._completion_callback()
            except Exception as e:
                logger.error(f"Controlador: Erro ao chamar completion_callback: {e}", exc_info=True)