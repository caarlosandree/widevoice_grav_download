import logging
import threading
import concurrent.futures
import os
from datetime import datetime

# Importa os módulos que contêm a lógica de API e download
from api_handler import construir_url_api, obter_dados_completos
from recording_downloader import baixar_gravacao, gerar_arquivo_metadado # Importa também gerar_arquivo_metadado para uso interno
import config # Importa config para o diretório padrão

logger = logging.getLogger(__name__)

# Número máximo de downloads paralelos (pode ser definido aqui ou passado na inicialização do controlador)
MAX_WORKERS = 5

class DownloadController:
    def __init__(self, status_callback=None, progress_callback=None, completion_callback=None, directory_getter=None):
        """
        Inicializa o controlador de download.

        Args:
            status_callback: Função a ser chamada para atualizar a mensagem de status na GUI.
            progress_callback: Função a ser chamada para atualizar o valor da barra de progresso na GUI.
            completion_callback: Função a ser chamada quando o processo de download terminar (sucesso ou falha).
            directory_getter: Função a ser chamada para obter o diretório de destino atual da GUI.
        """
        self._status_callback = status_callback
        self._progress_callback = progress_callback
        self._completion_callback = completion_callback
        self._directory_getter = directory_getter # Usado para obter o diretório de destino

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._is_running = False # Flag para indicar se o processo está ativo


    def start_download(self, url_base, login, token, datainicio_str, datafim_str):
        """
        Inicia o processo de download em uma thread separada.

        Args:
            url_base, login, token, datainicio_str, datafim_str: Dados da GUI necessários para a API.
        """
        if self._is_running:
            self._log_and_status("Aviso: O processo de download já está em execução.", level=logging.WARNING)
            return

        self._is_running = True
        self._log_and_status("Controlador: Processo de download iniciado.")
        logger.info("DownloadController: Método start_download chamado.")

        # Pega o diretório de destino através do getter fornecido pela GUI
        diretorio_destino = self._get_download_directory()
        if not diretorio_destino:
            self._log_and_status("Erro: Diretório de destino não especificado.", level=logging.ERROR)
            logger.error("DownloadController: Diretório de destino não obtido.")
            self._process_completed() # Finaliza o processo se o diretório não for válido
            return


        # Inicia a thread principal para orquestrar o download
        # A thread não bloqueará o método start_download, permitindo que a GUI responda.
        process_thread = threading.Thread(
             target=self._process_download_task,
             args=(url_base, login, token, datainicio_str, datafim_str, diretorio_destino)
         )
        process_thread.start()


    def _process_download_task(self, url_base, login, token, datainicio_str, datafim_str, diretorio_destino):
        """
        Tarefa principal de download executada na thread separada.
        Coordena a obtenção de dados da API e o download/processamento das gravações em paralelo.
        """
        logger.info("DownloadController: Thread de processamento principal iniciada.")
        try:
            # 1. Obter dados da API
            self._log_and_status("Controlador: Obtendo lista de chamadas da API...")
            url_api = construir_url_api(url_base, login, token)
            # Passa o callback de status para a função da API
            dados_chamadas = obter_dados_completos(url_api, datainicio_str, datafim_str, status_callback=self._log_and_status)

            if dados_chamadas is None:
                self._log_and_status("Controlador: Falha ao obter dados da API. Verifique logs para mais detalhes.", level=logging.ERROR)
                logger.error("DownloadController: Falha ao obter dados da API.")
                self._update_progress(0) # Reseta ou mantém progresso zero em caso de falha inicial
                return # Sai do método da thread


            if not isinstance(dados_chamadas, list) or not dados_chamadas:
                self._log_and_status("Controlador: Nenhum registro encontrado ou resposta da API em formato inesperado.", level=logging.WARNING)
                logger.info("DownloadController: Nenhum registro encontrado ou resposta da API em formato inesperado.")
                self._update_progress(100) # Considera "completo" se não há nada para processar
                return # Sai do método da thread

            total_chamadas = len(dados_chamadas)
            self._log_and_status(f"Controlador: Encontrados {total_chamadas} registros de chamadas para processar.")
            logger.info(f"DownloadController: Encontrados {total_chamadas} registros de chamadas.")

            self._update_progress_maximum(total_chamadas) # Define o máximo para a barra de progresso
            self._update_progress(0) # Inicia o progresso em zero

            processados_count = 0
            future_to_chamada = {}

            # 2. Submeter tarefas de download/processamento para o ThreadPoolExecutor
            self._log_and_status("Controlador: Iniciando processamento paralelo de gravações e metadados...")
            for chamada in dados_chamadas:
                 # Determina se a chamada tem gravação ou não
                 tem_gravacao = 'gravacao' in chamada and bool(chamada.get('gravacao'))

                 if tem_gravacao:
                      # Submete a tarefa de baixar_gravacao se tiver gravação
                      # Passa o callback de status
                      future = self._executor.submit(baixar_gravacao, url_base, chamada, diretorio_destino, self._log_and_status)
                      future_to_chamada[future] = (chamada, 'download') # Marca como tarefa de download
                 else:
                      # Submete a tarefa de processar_sem_gravacao se não tiver gravação
                      # Passa o callback de status e o diretório de destino (obtido via getter)
                      future = self._executor.submit(self._processar_sem_gravacao, chamada, self._log_and_status, diretorio_destino)
                      future_to_chamada[future] = (chamada, 'metadado_sem_gravacao') # Marca como tarefa de metadado sem gravação

            # 3. Monitorar a conclusão das tarefas
            self._log_and_status("Controlador: Aguardando conclusão das tarefas...")
            for future in concurrent.futures.as_completed(future_to_chamada):
                processados_count += 1
                self._update_progress(processados_count) # Atualiza a barra de progresso a cada tarefa concluída

                chamada_info = future_to_chamada[future]
                chamada_original = chamada_info[0]
                tipo_tarefa = chamada_info[1]
                chamada_id = chamada_original.get('id', 'desconhecido')

                try:
                    # Tenta obter o resultado do future. Isso irá levantar a exceção se uma ocorreu na tarefa.
                    # O resultado (True/False) já foi tratado dentro de baixar_gravacao ou _processar_sem_gravacao
                    result = future.result()
                    if tipo_tarefa == 'download' and result is False:
                         logger.warning(f"DownloadController: Tarefa de download falhou para Chamada ID {chamada_id}.")
                    elif tipo_tarefa == 'metadado_sem_gravacao' and result is False:
                         logger.warning(f"DownloadController: Tarefa de gerar metadado para Chamada ID {chamada_id} (sem gravação) falhou.")

                except Exception as exc:
                    # Captura exceções não tratadas dentro das funções submitidas
                    mensagem_erro = f"Controlador: Ocorreu uma exceção não tratada ao processar a chamada ID {chamada_id}: {exc}"
                    self._log_and_status(mensagem_erro, level=logging.ERROR)
                    logger.exception(f"DownloadController: Exceção não tratada ao processar chamada ID {chamada_id}")

            # 4. Resumo e Finalização
            # Após todos os futures serem concluídos, recontamos sucessos e falhas
            gravacoes_baixadas_count = 0
            erros_download_count = 0
            processados_sem_gravacao_count = 0
            erros_metadado_sem_gravacao_count = 0

            for future in future_to_chamada:
                 chamada_info = future_to_chamada[future]
                 tipo_tarefa = chamada_info[1]

                 try:
                     result = future.result() # Tenta obter o resultado (True/False) ou levanta exceção se não tratada

                     if tipo_tarefa == 'download':
                          if result is True:
                               gravacoes_baixadas_count += 1
                          else: # result is False ou exceção não tratada
                               erros_download_count += 1
                               # O logging já ocorreu no loop anterior ou dentro da função baixar_gravacao
                     elif tipo_tarefa == 'metadado_sem_gravacao':
                          if result is True:
                               processados_sem_gravacao_count += 1
                          else: # result is False ou exceção não tratada
                               erros_metadado_sem_gravacao_count += 1
                               # O logging já ocorreu no loop anterior ou dentro da função _processar_sem_gravacao

                 except Exception:
                      # Se uma exceção ocorreu aqui, significa que não foi tratada antes.
                      # Dependendo do tipo de tarefa, contamos como erro.
                      if tipo_tarefa == 'download':
                           erros_download_count += 1
                           logger.error(f"DownloadController: Exceção não tratada re-capturada para tarefa de download.")
                      elif tipo_tarefa == 'metadado_sem_gravacao':
                           erros_metadado_sem_gravacao_count += 1
                           logger.error(f"DownloadController: Exceção não tratada re-capturada para tarefa de metadado sem gravação.")
                      # O log original da exceção já ocorreu no loop as_completed


            self._log_and_status("\n--- Processo Finalizado ---")
            self._log_and_status(f"Controlador: Total de registros da API encontrados: {total_chamadas}")
            self._log_and_status(f"Controlador: Total de registros processados (baixados ou metadado gerado): {processados_count}")
            self._log_and_status(f"Controlador: Gravações baixadas com sucesso: {gravacoes_baixadas_count}")
            self._log_and_status(f"Controlador: Registros sem gravação processados: {processados_sem_gravacao_count}")

            if erros_download_count > 0:
                self._log_and_status(f"Controlador: Erros durante o download de gravações: {erros_download_count}", level=logging.WARNING)
                self._log_and_status("Controlador: Verifique as mensagens de erro acima e os logs para detalhes.")
                logger.warning(f"DownloadController: Processo finalizado com {erros_download_count} erros de download.")

            if erros_metadado_sem_gravacao_count > 0:
                self._log_and_status(f"Controlador: Erros ao processar registros sem gravação (geração de metadado): {erros_metadado_sem_gravacao_count}", level=logging.WARNING)
                self._log_and_status("Controlador: Verifique as mensagens de erro acima e os logs para detalhes.")
                logger.warning(f"DownloadController: Processo finalizado com {erros_metadado_sem_gravacao_count} erros ao processar registros sem gravação.")


            if erros_download_count == 0 and erros_metadado_sem_gravacao_count == 0:
                 self._log_and_status("Controlador: Todos os registros foram processados sem erros.")
                 logger.info("DownloadController: Processo finalizado com sucesso (sem erros relatados nas tarefas individuais).")


            self._update_progress(total_chamadas) # Garante que a barra chegue a 100% se o total for > 0


        except Exception as e:
            # Captura qualquer erro inesperado na própria thread de processamento principal
            mensagem_erro_inesperado = f"Controlador: Ocorreu um erro inesperado durante o processamento principal: {e}"
            self._log_and_status(mensagem_erro_inesperado, level=logging.ERROR)
            logger.exception("DownloadController: Erro inesperado durante o processamento principal.")

        finally:
            self._is_running = False # Reseta a flag ao final do processo
            self._process_completed() # Chama o callback de conclusão

    def _processar_sem_gravacao(self, chamada, status_callback, diretorio_raiz):
        """
        Método auxiliar executado em threadpool para processar chamadas sem gravação.
        Gera apenas o metadado e retorna True para indicar que foi "processada".

        Args:
            chamada: Dicionário com os dados da chamada da API.
            status_callback: Função para atualizar o status (passada para gerar_arquivo_metadado).
            diretorio_raiz: O diretório base de destino (obtido via getter).
        """
        chamada_id = chamada.get('id', 'desconhecido')
        numero_chamada = chamada.get('numero', 'desconhecido')
        datahora_chamada = chamada.get('datahora', 'desconhecido')

        # Use a datahora original da chamada para o nome do arquivo de metadado
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
                  # Se datahora_str estiver vazio ou inválido, o warning já é logado.
                  pass
        except (ValueError, TypeError):
             logger.warning(f"DownloadController: Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00) para metadado sem gravação.")

        # Usa o diretorio_raiz passado como argumento
        if not diretorio_raiz:
            # Fallback para o diretório do config se o argumento estiver vazio (não deveria acontecer)
             diretorio_raiz = config.DIRETORIO_BASE_GRAVACOES
             logger.warning(f"DownloadController: Diretório raiz vazio para Chamada ID {chamada_id}. Usando diretório do config: {diretorio_raiz}")


        diretorio_destino_dia = os.path.join(diretorio_raiz, ano, mes_str, dia_str)
        try:
             os.makedirs(diretorio_destino_dia, exist_ok=True)
        except Exception as e:
             logger.error(f"DownloadController: Erro ao criar diretórios para metadado sem gravação (ID {chamada_id}, Dir: {diretorio_destino_dia}): {e}", exc_info=True)
             # Retorna False se não puder criar os diretórios para salvar o metadado
             return False


        nome_arquivo_base = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}"
        # Nome do arquivo de METADADO para chamadas SEM GRAVAÇÃO:
        # ANO_MES_DIA_NUMERO_HORAMINUTOSEGUNDO_ID_METADADO_SEM_GRAVACAO.txt
        caminho_arquivo_metadado_sem_gravacao = os.path.join(diretorio_destino_dia, f"{nome_arquivo_base}_METADADO_SEM_GRAVACAO.txt")

        try:
            mensagem = f"Chamada: Número {numero_chamada} em {datahora_chamada} (ID {chamada_id}) - Não possui gravação. Gerando apenas metadado: {os.path.basename(caminho_arquivo_metadado_sem_gravacao)}"
            # Usa o status_callback passado como argumento
            if status_callback:
                 status_callback(mensagem)
            logger.info(f"DownloadController: {mensagem}")

            # Chama gerar_arquivo_metadado passando o dicionário completo da chamada e o callback
            gerar_arquivo_metadado(chamada, caminho_arquivo_metadado_sem_gravacao, status_callback)
            return True # Indica sucesso no processamento sem gravação

        except Exception as e:
            mensagem_erro_metadado = f"DownloadController: Erro inesperado ao tentar gerar metadado para Chamada ID {chamada_id} sem gravação: {e}"
            # Usa o status_callback passado como argumento
            if status_callback:
                status_callback(mensagem_erro_metadado)
            logger.error(mensagem_erro_metadado, exc_info=True)
            return False # Indica falha no processamento mesmo sem gravação

    def _log_and_status(self, message, level=logging.INFO):
        """Loga a mensagem e chama o callback de status se estiver disponível, passando o nível."""
        if level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        # Adicione outros níveis conforme necessário

        if self._status_callback:
            try:
                # Chama o callback da GUI, passando a mensagem E o nível de log
                self._status_callback(f"[CTL] {message}", level)
            except Exception as e:
                logger.error(f"DownloadController: Erro ao chamar status_callback: {e} - Mensagem: {message}",
                             exc_info=True)

    def _update_progress(self, value):
        """Chama o callback de progresso se estiver disponível."""
        if self._progress_callback:
            try:
                self._progress_callback(value)
            except Exception as e:
                logger.error(f"DownloadController: Erro ao chamar progress_callback: {e} - Valor: {value}", exc_info=True)

    def _update_progress_maximum(self, maximum):
        """Define o valor máximo para a barra de progresso (se a GUI suportar)."""
        # A atualização do 'maximum' da barra de progresso geralmente precisa ser feita na thread principal da GUI.
        # O DownloadController não deve manipular diretamente widgets da GUI.
        # Em uma arquitetura ideal, a GUI monitoraria algum estado no controlador
        # ou o controlador enviaria um sinal específico para a GUI atualizar o máximo.
        # Como alternativa simples AGORA, você pode adicionar um callback para isso
        # na inicialização do DownloadController ou ter a GUI observando o estado.
        # Por enquanto, esta função é apenas um placeholder e não faz nada diretamente
        # na GUI. A GUI (WidevoiceDownloaderGUI) ainda precisará definir o máximo
        # antes de iniciar o download, baseada nas informações que receberia do controlador
        # (talvez após a chamada à API).

        # Implementação temporária: loga a informação
        logger.debug(f"DownloadController: Solicitada atualização do máximo da barra de progresso para: {maximum}")
        # **Nota:** A GUI ainda precisa chamar self.progress_bar['maximum'] = total_chamadas
        # na thread principal, após obter o total_chamadas do controlador.

    def _get_download_directory(self):
        """Chama a função getter para obter o diretório de destino da GUI."""
        if self._directory_getter:
            try:
                return self._directory_getter()
            except Exception as e:
                logger.error(f"DownloadController: Erro ao chamar directory_getter: {e}", exc_info=True)
                return None
        logger.warning("DownloadController: directory_getter não configurado.")
        return None


    def _process_completed(self):
        """Chama o callback de conclusão se estiver disponível."""
        logger.info("DownloadController: Processo de download concluído.")
        if self._completion_callback:
            try:
                self._completion_callback() # A GUI usará este callback para habilitar os botões
            except Exception as e:
                logger.error(f"DownloadController: Erro ao chamar completion_callback: {e}", exc_info=True)