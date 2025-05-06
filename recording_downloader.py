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

def gerar_arquivo_metadado(chamada, caminho_arquivo_gravacao, status_callback=None):
    """
    Gera um arquivo TXT com os metadados da chamada.
    Salva no mesmo diretório da gravação.
    """
    try:
        # Derivar o nome do arquivo de metadado do nome do arquivo de gravação
        base, _ = os.path.splitext(caminho_arquivo_gravacao)
        caminho_arquivo_metadado = base + ".txt"

        # Formatar os metadados
        # Iteramos sobre todos os itens no dicionário da chamada e formatamos
        metadata_content = "--- Metadados da Chamada ---\n"
        for key, value in chamada.items():
            # Formata cada par chave-valor
            metadata_content += f"{key.replace('_', ' ').capitalize()}: {value}\n" # Substitui _ por espaço e capitaliza

        # Escrever no arquivo
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
            status_callback(mensagem_erro)
        logger.error(mensagem_erro, exc_info=True)


# Adicionamos diretorio_base como um parâmetro opcional
def baixar_gravacao(url_base, chamada, diretorio_base=None, status_callback=None):
    """
    Baixa um arquivo de gravação para o diretório local com tentativas.
    diretorio_base: O diretório base para salvar as gravações (substitui o do config.py).
    status_callback é uma função opcional para reportar o status na GUI.
    As mensagens importantes também serão logadas.
    """
    # Verifica se a chamada possui o campo 'gravacao'
    if 'gravacao' not in chamada or not chamada['gravacao']:
        # Se não tiver gravação, reporta e retorna True (processado, mas sem download)
        chamada_id = chamada.get('id', 'desconhecido')
        numero_chamada = chamada.get('numero', 'desconhecido')
        datahora_chamada = chamada.get('datahora', 'desconhecido')
        mensagem = f"Chamada: Número {numero_chamada} em {datahora_chamada} (ID {chamada_id}) - Não possui gravação. Gerando apenas metadado."
        if status_callback:
             status_callback(mensagem)
        logger.info(mensagem)

        # Tenta gerar o metadado mesmo sem gravação
        try:
            # Define um caminho base para o arquivo de metadado quando não há gravação
            # Usaremos o diretório de destino e um nome baseado nos dados da chamada
            datahora_str = chamada.get('datahora', '')
            data_chamada = None
            ano, mes_str, dia_str = "0000", "00", "00"
            hora_min_seg = "000000"

            try:
                 if datahora_str:
                      data_chamada = datetime.datetime.strptime(datahora_str, '%Y-%m-%d %H:%M:%S')
                      ano = str(data_chamada.year)
                      mes_str = f"{data_chamada.month:02d}"
                      dia_str = f"{data_chamada.day:02d}"
                      hora_min_seg = data_chamada.strftime('%H%M%S')
                 else:
                      raise ValueError("Campo 'datahora' vazio.")
            except (ValueError, TypeError):
                 logger.warning(f"Formato de data/hora inválido ou ausente para a chamada com ID {chamada_id}. Usando data padrão (0000/00/00) para metadado sem gravação.")


            diretorio_raiz = diretorio_base if diretorio_base else config.DIRETORIO_BASE_GRAVACOES
            diretorio_destino = os.path.join(diretorio_raiz, ano, mes_str, dia_str)
            os.makedirs(diretorio_destino, exist_ok=True)

            nome_arquivo_base = f"{ano}_{mes_str}_{dia_str}_{numero_chamada}_{hora_min_seg}_{chamada_id}"
            caminho_arquivo_metadado_sem_gravacao = os.path.join(diretorio_destino, f"{nome_arquivo_base}_METADADO_SEM_GRAVACAO.txt")

            # Gera o arquivo de metadado usando o caminho temporário
            gerar_arquivo_metadado(chamada, caminho_arquivo_metadado_sem_gravacao, status_callback)

        except Exception as e:
            mensagem_erro_metadado = f"Erro inesperado ao tentar gerar metadado para Chamada ID {chamada_id} sem gravação: {e}"
            if status_callback:
                status_callback(mensagem_erro_metadado)
            logger.error(mensagem_erro_metadado, exc_info=True)


        return True # Consideramos processado mesmo sem gravação

    # --- Continua a lógica de download APENAS SE HOUVER GRAVAÇÃO ---
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

    # Formato do nome do arquivo de GRAVAÇÃO: ANO_MES_DIA_NUMERO_HORAMINUTOSEGUNDO_ID.gsm
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

            # ** CHAMA A FUNÇÃO PARA GERAR O ARQUIVO DE METADADO AQUI APÓS SUCESSO **
            gerar_arquivo_metadado(chamada, caminho_arquivo_local, status_callback)

            return True # Retorna True em caso de sucesso

        except requests.exceptions.HTTPError as e:
            mensagem_erro = f"Erro HTTP ({e.response.status_code} - {e.response.reason}) ao baixar gravação {url_gravacao} (Chamada ID {chamada_id}). Não será retentado."
            if status_callback:
                status_callback(mensagem_erro)
            logger.error(mensagem_erro, exc_info=True) # Loga erro com traceback
            # Mesmo em caso de erro HTTP, tentamos gerar o metadado para registrar a falha do download
            try:
                 gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_DOWNLOAD_FAILED.txt", status_callback)
            except Exception as meta_e:
                 logger.error(f"Erro adicional ao gerar metadado de falha para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
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
                # Tenta gerar o metadado mesmo após falhas de retentativa
                try:
                     gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_DOWNLOAD_FAILED.txt", status_callback)
                except Exception as meta_e:
                     logger.error(f"Erro adicional ao gerar metadado de falha final para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
                return False # Retorna False se todas as tentativas falharem

        except Exception as e:
            # Trata quaisquer outros erros inesperados durante o download/processamento
            mensagem_erro_inesperado = f"Ocorreu um erro inesperado ao processar gravação da Chamada ID {chamada_id}: {e}"
            if status_callback:
                status_callback(mensagem_erro_inesperado)
            logger.exception(mensagem_erro_inesperado) # Loga erro com traceback usando exception()
            # Tenta gerar o metadado mesmo em caso de erro inesperado
            try:
                 gerar_arquivo_metadado(chamada, caminho_arquivo_local + "_PROCESS_ERROR.txt", status_callback)
            except Exception as meta_e:
                 logger.error(f"Erro adicional ao gerar metadado de erro inesperado para Chamada ID {chamada_id}: {meta_e}", exc_info=True)
            return False # Erros inesperados geralmente não devem ser retentados

    # Se o loop terminar sem sucesso (improvável com o return False nos excepts, mas por garantia)
    logger.error(f"Função baixar_gravacao terminou sem retornar para Chamada ID {chamada_id}. Considerado falha.")
    return False