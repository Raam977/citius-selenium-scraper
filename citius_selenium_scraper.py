#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para web scraping do Portal Citius utilizando Selenium WebDriver
Permite pesquisar por NIF/designação com intervalo de datas
"""

import os
import sys
import time
import logging
import argparse
import csv
import json
import datetime
import re
import traceback
from urllib.parse import urljoin
from collections import defaultdict

# Instalar dependências se não estiverem presentes
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Instalando dependências necessárias...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
    from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("citius_scraper.log")
    ]
)
logger = logging.getLogger(__name__)

# Banner do aplicativo
BANNER = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║    ██████╗██╗████████╗██╗██╗   ██╗███████╗    ███████╗ ██████╗██████╗    ║
║   ██╔════╝██║╚══██╔══╝██║██║   ██║██╔════╝    ██╔════╝██╔════╝██╔══██╗   ║
║   ██║     ██║   ██║   ██║██║   ██║███████╗    ███████╗██║     ██████╔╝   ║
║   ██║     ██║   ██║   ██║██║   ██║╚════██║    ╚════██║██║     ██╔══██╗   ║
║   ╚██████╗██║   ██║   ██║╚██████╔╝███████║    ███████║╚██████╗██║  ██║   ║
║    ╚═════╝╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝   ║
║                                                                           ║
║                Web Scraper para o Portal Citius (Selenium)                ║
║                v1.0.0 - Desenvolvido em Python                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

MANUAL = """
╔════════════════════════════════════════════════════════════════╗
║                    MANUAL - CITIUS SELENIUM SCRAPER           ║
╚════════════════════════════════════════════════════════════════╝

Este script permite automatizar a pesquisa e recolha de processos no Portal Citius utilizando Selenium.

FUNCIONALIDADES:
- Pesquisa por NIF/NIPC ou designação
- Intervalo de datas personalizável
- Filtros por tribunal, grupo de actos e acto
- Filtros temporais (15, 30 dias ou todos)
- Resultados exportados em CSV e/ou JSON

DEPENDÊNCIAS:
- Python >= 3.6
- Chrome ou Chromium
- Bibliotecas: selenium, webdriver-manager

INSTALAÇÃO:
    pip install selenium webdriver-manager

USO:
    python citius_selenium_scraper.py [opções]

OPÇÕES:
  --nif               NIF/NIPC da entidade
  --designacao        Nome/designação da entidade
  --data-inicio       Data de início (formato DD-MM-YYYY)
  --data-fim          Data de fim (formato DD-MM-YYYY)
  --tribunal          'nova' ou 'extintos'
  --grupo-actos       Grupo de actos
  --acto              Acto específico
  --dias              15 | 30 | todos (padrão: todos)
  --output            Nome base do ficheiro (sem extensão)
  --headless          Modo sem interface gráfica
  --debug             Mostrar logs detalhados
  --timeout           Tempo máximo de espera (segundos)
  --man               Mostrar este manual e sair
  -h, --help          Mostrar ajuda resumida

EXEMPLOS:
  python citius_selenium_scraper.py --nif 12345678
  python citius_selenium_scraper.py --designacao "Empresa XYZ" --data-inicio "01-01-2025" --data-fim "31-01-2025"

NOTA:
Este script é fornecido para fins educacionais. Respeita os termos de uso do Portal Citius.
"""





class CitiusSeleniumScraper:
    """Classe para fazer web scraping do Portal Citius usando Selenium WebDriver"""
    
    def __init__(self, headless=True, debug=False, timeout=60):
        """
        Inicializa o scraper com o WebDriver e configurações
        
        Args:
            headless (bool): Se True, executa o navegador em modo headless (sem interface gráfica)
            debug (bool): Se True, ativa o modo de debug com mais logs
            timeout (int): Tempo máximo de espera em segundos para operações
        """
        self.base_url = "https://www.citius.mj.pt/portal/consultas/consultascire.aspx"
        self.results_url = "https://www.citius.mj.pt/portal/consultas/ConsultasCire.aspx"
        self.timeout = timeout
        
        # Configurar o nível de logging
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Modo de debug ativado")
        
        # Configurar opções do Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        
        # Inicializar o WebDriver
        try:
            print("Inicializando o WebDriver...")
            
            # Obter a versão do Chrome instalado
            chrome_version = self.get_chrome_version()
            if chrome_version:
                print(f"Versão do Chrome/Chromium detectada: {chrome_version}")
                logger.info(f"Versão do Chrome/Chromium detectada: {chrome_version}")
                
                # Inicializar o WebDriver com a versão compatível
                # Usar o ChromeDriverManager padrão, que deve detectar a versão correta
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            else:
                # Fallback para o método padrão se não conseguir detectar a versão
                print("Não foi possível detectar a versão do Chrome. Usando configuração padrão.")
                logger.warning("Não foi possível detectar a versão do Chrome. Usando configuração padrão.")
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            
            self.driver.implicitly_wait(10)  # Espera implícita de 10 segundos
            logger.info("WebDriver inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar o WebDriver: {e}")
            logger.error(f"Erro ao inicializar o WebDriver: {e}")
            
            # Tentar método alternativo com driver local
            try:
                print("Tentando método alternativo com driver local...")
                # Usar o driver do sistema
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
                logger.info("WebDriver inicializado com sucesso usando método alternativo")
            except Exception as e2:
                print(f"Erro ao inicializar o WebDriver com método alternativo: {e2}")
                logger.error(f"Erro ao inicializar o WebDriver com método alternativo: {e2}")
                raise
    
    def get_chrome_version(self):
        """
        Detecta a versão do Chrome/Chromium instalada no sistema
        
        Returns:
            str: Versão do Chrome/Chromium ou None se não for possível detectar
        """
        try:
            # Tentar diferentes comandos para detectar a versão do Chrome/Chromium
            commands = [
                "chromium-browser --version",
                "chromium --version",
                "google-chrome --version",
                "chrome --version"
            ]
            
            for cmd in commands:
                try:
                    import subprocess
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                    output = output.decode('utf-8').strip()
                    
                    # Extrair a versão usando regex
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+|\d+\.\d+\.\d+)', output)
                    if match:
                        return match.group(1)
                except:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Erro ao detectar versão do Chrome: {e}")
            return None
    
    def __del__(self):
        """Método destrutor para garantir que o WebDriver seja fechado"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                logger.info("WebDriver fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar o WebDriver: {e}")
    
    def wait_for_element(self, by, value, timeout=None):
        """
        Espera até que um elemento esteja presente na página
        
        Args:
            by (By): Método de localização (By.ID, By.XPATH, etc.)
            value (str): Valor para localizar o elemento
            timeout (int): Tempo máximo de espera em segundos
            
        Returns:
            WebElement: Elemento encontrado ou None se não encontrado
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout ao esperar pelo elemento {by}={value}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao esperar pelo elemento {by}={value}: {e}")
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """
        Espera até que um elemento esteja clicável na página
        
        Args:
            by (By): Método de localização (By.ID, By.XPATH, etc.)
            value (str): Valor para localizar o elemento
            timeout (int): Tempo máximo de espera em segundos
            
        Returns:
            WebElement: Elemento encontrado ou None se não encontrado
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout ao esperar pelo elemento clicável {by}={value}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao esperar pelo elemento clicável {by}={value}: {e}")
            return None
    
    def open_search_page(self):
        """
        Abre a página de pesquisa do Portal Citius
        
        Returns:
            bool: True se a página foi aberta com sucesso, False caso contrário
        """
        try:
            print("Abrindo página de pesquisa do Portal Citius...")
            self.driver.get(self.base_url)
            
            # Verificar se a página carregou corretamente
            if self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_txtPesquisa"):
                logger.info("Página de pesquisa aberta com sucesso")
                return True
            else:
                print("Erro ao carregar a página de pesquisa")
                logger.error("Erro ao carregar a página de pesquisa")
                return False
        except Exception as e:
            print(f"Erro ao abrir a página de pesquisa: {e}")
            logger.error(f"Erro ao abrir a página de pesquisa: {e}")
            return False
    
    def fill_search_form(self, nif=None, designacao=None, data_inicio=None, data_fim=None, 
                         tribunal=None, grupo_actos=None, acto=None, dias="todos"):
        """
        Preenche o formulário de pesquisa com os parâmetros fornecidos
        
        Args:
            nif (str): NIF/NIPC para pesquisa
            designacao (str): Designação para pesquisa
            data_inicio (str): Data de início no formato DD-MM-YYYY
            data_fim (str): Data de fim no formato DD-MM-YYYY
            tribunal (str): Tribunal para filtrar (True para "Tribunais Extintos", False para "Nova Estrutura Judiciária")
            grupo_actos (str): Grupo de actos para filtrar
            acto (str): Acto específico para filtrar
            dias (str): Filtro de dias ('15', '30', 'todos')
            
        Returns:
            bool: True se o formulário foi preenchido com sucesso, False caso contrário
        """
        try:
            # Validar parâmetros
            if not nif and not designacao:
                print("É necessário fornecer NIF ou designação para pesquisa")
                logger.error("É necessário fornecer NIF ou designação para pesquisa")
                return False
            
            # Preencher campo de pesquisa (NIF ou designação)
            if nif:
                # Preencher campo de pesquisa com o NIF
                pesquisa_input = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_txtPesquisa")
                if pesquisa_input:
                    pesquisa_input.clear()
                    pesquisa_input.send_keys(nif)
                    print(f"Pesquisando por NIF/NIPC: {nif}")
                    logger.info(f"Pesquisando por NIF/NIPC: {nif}")
                    
                    # Selecionar opção NIF/NIPC
                    nif_radio = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_rblTipo_0")
                    if nif_radio:
                        nif_radio.click()
                        logger.info("Opção NIF/NIPC selecionada")
                    else:
                        logger.warning("Não foi possível selecionar a opção NIF/NIPC")
                else:
                    logger.error("Campo de pesquisa não encontrado")
                    return False
            elif designacao:
                # Preencher campo de pesquisa com a designação
                pesquisa_input = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_txtPesquisa")
                if pesquisa_input:
                    pesquisa_input.clear()
                    pesquisa_input.send_keys(designacao)
                    print(f"Pesquisando por designação: {designacao}")
                    logger.info(f"Pesquisando por designação: {designacao}")
                    
                    # Selecionar opção Designação
                    designacao_radio = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_rblTipo_1")
                    if designacao_radio:
                        designacao_radio.click()
                        logger.info("Opção Designação selecionada")
                    else:
                        logger.warning("Não foi possível selecionar a opção Designação")
                else:
                    logger.error("Campo de pesquisa não encontrado")
                    return False
            
            # Preencher data de início se fornecida
            if data_inicio:
                data_inicio_input = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_txtCalendarDesde")
                if data_inicio_input:
                    data_inicio_input.clear()
                    data_inicio_input.send_keys(data_inicio)
                    print(f"Data início: {data_inicio}")
                    logger.info(f"Data início: {data_inicio}")
                else:
                    logger.warning("Campo de data início não encontrado")
            
            # Preencher data de fim se fornecida
            if data_fim:
                data_fim_input = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_txtCalendarAte")
                if data_fim_input:
                    data_fim_input.clear()
                    data_fim_input.send_keys(data_fim)
                    print(f"Data fim: {data_fim}")
                    logger.info(f"Data fim: {data_fim}")
                else:
                    logger.warning("Campo de data fim não encontrado")
            
            # Selecionar tipo de tribunal se fornecido
            if tribunal is not None:
                if tribunal:  # True para "Tribunais Extintos"
                    tribunal_radio = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_rbtlTribunais_1")
                    if tribunal_radio:
                        tribunal_radio.click()
                        print("Filtro de tribunal: Tribunais Extintos")
                        logger.info("Filtro de tribunal: Tribunais Extintos")
                        
                        # Aguardar o carregamento da lista de tribunais extintos
                        time.sleep(2)
                    else:
                        logger.warning("Opção de Tribunais Extintos não encontrada")
                else:  # False para "Nova Estrutura Judiciária"
                    tribunal_radio = self.wait_for_element(By.ID, "ctl00_ContentPlaceHolder1_rbtlTribunais_0")
                    if tribunal_radio:
                        tribunal_radio.click()
                        print("Filtro de tribunal: Nova Estrutura Judiciária")
                        logger.info("Filtro de tribunal: Nova Estrutura Judiciária")
                        
                        # Aguardar o carregamento da lista de tribunais
                        time.sleep(2)
                    else:
                        logger.warning("Opção de Nova Estrutura Judiciária não encontrada")
            
            # Selecionar grupo de actos se fornecido
            if grupo_actos:
                try:
                    grupo_actos_select = Select(self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlGrupoActos"))
                    grupo_actos_select.select_by_visible_text(grupo_actos)
                    print(f"Grupo de actos: {grupo_actos}")
                    logger.info(f"Grupo de actos: {grupo_actos}")
                    
                    # Aguardar o carregamento da lista de actos
                    time.sleep(2)
                except (NoSuchElementException, ElementNotInteractableException) as e:
                    logger.warning(f"Erro ao selecionar grupo de actos: {e}")
            
            # Selecionar acto específico se fornecido
            if acto:
                try:
                    acto_select = Select(self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlActos"))
                    acto_select.select_by_visible_text(acto)
                    print(f"Acto específico: {acto}")
                    logger.info(f"Acto específico: {acto}")
                except (NoSuchElementException, ElementNotInteractableException) as e:
                    logger.warning(f"Erro ao selecionar acto específico: {e}")
            
            # Configurar filtro de dias
            if dias:
                dias_id_map = {
                    "15": "ctl00_ContentPlaceHolder1_rblDias_0",
                    "30": "ctl00_ContentPlaceHolder1_rblDias_1",
                    "todos": "ctl00_ContentPlaceHolder1_rblDias_2"
                }
                
                dias_id = dias_id_map.get(dias.lower())
                if dias_id:
                    dias_radio = self.wait_for_element(By.ID, dias_id)
                    if dias_radio:
                        dias_radio.click()
                        print(f"Filtro de dias: {dias}")
                        logger.info(f"Filtro de dias: {dias}")
                    else:
                        logger.warning(f"Opção de dias '{dias}' não encontrada")
                else:
                    logger.warning(f"Filtro de dias '{dias}' não reconhecido")
            
            return True
        except Exception as e:
            print(f"Erro ao preencher o formulário: {e}")
            logger.error(f"Erro ao preencher o formulário: {e}")
            return False
    
    def submit_search(self):
        """
        Submete o formulário de pesquisa
        
        Returns:
            bool: True se a pesquisa foi submetida com sucesso, False caso contrário
        """
        try:
            print("Submetendo pesquisa...")
            
            # Clicar no botão de pesquisa
            search_button = self.wait_for_element_clickable(By.ID, "ctl00_ContentPlaceHolder1_btnSearch")
            if search_button:
                search_button.click()
                logger.info("Botão de pesquisa clicado")
                
                # Aguardar o carregamento dos resultados
                time.sleep(5)
                
                # Verificar se a página de resultados carregou
                if "documentos encontrados" in self.driver.page_source:
                    print("Pesquisa submetida com sucesso")
                    logger.info("Pesquisa submetida com sucesso")
                    return True
                else:
                    # Verificar se há mensagem de erro ou sem resultados
                    no_results = self.driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_lblNoResults")
                    if no_results and no_results[0].is_displayed():
                        print(f"Sem resultados: {no_results[0].text.strip()}")
                        logger.info(f"Mensagem de sem resultados: {no_results[0].text.strip()}")
                        return True
                    
                    # Verificar se há mensagem de erro de validação
                    validation_errors = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='color:Red']")
                    if validation_errors:
                        for error in validation_errors:
                            if error.is_displayed():
                                print(f"Erro de validação: {error.text.strip()}")
                                logger.error(f"Erro de validação: {error.text.strip()}")
                        return False
                    
                    print("Página de resultados carregada, mas formato não reconhecido")
                    logger.warning("Página de resultados carregada, mas formato não reconhecido")
                    return True
            else:
                print("Botão de pesquisa não encontrado")
                logger.error("Botão de pesquisa não encontrado")
                return False
        except Exception as e:
            print(f"Erro ao submeter a pesquisa: {e}")
            logger.error(f"Erro ao submeter a pesquisa: {e}")
            return False
    
    def extract_results(self, max_extraction_time=800):
        """
        Extrai os resultados da página com timeout para evitar bloqueios
        
        Args:
            max_extraction_time (int): Tempo máximo em segundos para extração
            
        Returns:
            list: Lista de dicionários com os resultados
        """
        results = []
        total_docs = 0
        
        try:
            print("Extraindo resultados...")
            
            # Definir tempo limite para extração
            start_time = time.time()
            
            # Verificar se há mensagem de total de documentos encontrados
            total_docs_div = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'documentos encontrados')]")
            if total_docs_div:
                total_docs_text = total_docs_div[0].text.strip()
                match = re.search(r'(\d+)', total_docs_text)
                if match:
                    total_docs = int(match.group(1))
                    print(f"Total de documentos encontrados: {total_docs}")
                    logger.info(f"Total de documentos encontrados: {total_docs}")
                    
                    # Se não houver resultados, retornar lista vazia
                    if total_docs == 0:
                        print("Nenhum resultado encontrado")
                        logger.info("Nenhum resultado encontrado")
                        return results
            
            # Método 1: Tentar encontrar a tabela de resultados tradicional
            try:
                result_table = self.driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_gvResults")
                if result_table and len(result_table) > 0:
                    print("Tabela de resultados tradicional encontrada")
                    logger.info("Tabela de resultados tradicional encontrada")
                    
                    # Extrair linhas da tabela
                    rows = self.driver.find_elements(By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_gvResults']/tbody/tr")
                    
                    # Ignorar a primeira linha (cabeçalho)
                    if len(rows) > 1:
                        print(f"Processando {len(rows)-1} resultados da tabela...")
                        
                        for i in range(1, len(rows)):
                            # Verificar timeout
                            if time.time() - start_time > max_extraction_time:
                                print(f"Timeout de extração atingido após processar {i} de {len(rows)-1} linhas")
                                logger.warning(f"Timeout de extração atingido após processar {i} de {len(rows)-1} linhas")
                                break
                                
                            try:
                                row = rows[i]
                                cells = row.find_elements(By.TAG_NAME, "td")
                                
                                if len(cells) >= 5:
                                    result = {}
                                    
                                    # Extrair dados das células
                                    result['Tribunal'] = cells[0].text.strip()
                                    result['Processo'] = cells[1].text.strip()
                                    result['Data'] = cells[2].text.strip()
                                    result['Ato'] = cells[3].text.strip()
                                    result['Descrição'] = cells[4].text.strip()
                                    
                                    # Verificar se há links para documentos
                                    links = cells[4].find_elements(By.TAG_NAME, "a")
                                    if links:
                                        result['Links'] = []
                                        for link in links:
                                            href = link.get_attribute("href")
                                            if href:
                                                result['Links'].append(href)
                                    
                                    results.append(result)
                            except StaleElementReferenceException:
                                logger.warning(f"Elemento ficou obsoleto durante a extração da linha {i}")
                                continue
                            except Exception as e:
                                logger.warning(f"Erro ao processar linha {i}: {e}")
                                continue
                        
                        # Se encontramos resultados na tabela, retornar
                        if len(results) > 0:
                            return results
                    
            except Exception as e:
                logger.warning(f"Erro ao processar tabela de resultados: {e}")
            
            # Método 2: Tentar encontrar resultados em formato de lista/div
            try:
                # Verificar se há div de resultados
                results_div = self.driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_divResultados")
                if results_div and len(results_div) > 0:
                    print("Div de resultados encontrada")
                    logger.info("Div de resultados encontrada")
                    
                    # Encontrar todos os itens de resultado
                    # Usar XPath mais abrangente para capturar todos os tipos de resultados
                    result_items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'resultadocdital') or contains(@class, 'resultado')]")
                    
                    if not result_items or len(result_items) == 0:
                        # Tentar outro seletor se o primeiro falhar
                        result_items = self.driver.find_elements(By.CSS_SELECTOR, ".resultadocdital, .resultado, div[id*='divResultado']")
                    
                    if not result_items or len(result_items) == 0:
                        # Último recurso: procurar por divs dentro da div de resultados
                        result_items = results_div[0].find_elements(By.XPATH, ".//div[contains(@id, 'divResultado')]")
                    
                    if result_items and len(result_items) > 0:
                        print(f"Processando {len(result_items)} itens de resultado...")
                        
                        for i, item in enumerate(result_items):
                            # Verificar timeout
                            if time.time() - start_time > max_extraction_time:
                                print(f"Timeout de extração atingido após processar {i} de {len(result_items)} itens")
                                logger.warning(f"Timeout de extração atingido após processar {i} de {len(result_items)} itens")
                                break
                                
                            try:
                                result = {}
                                
                                # Extrair informações por campos específicos
                                try:
                                    # Tribunal
                                    tribunal_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblTribunal')]")
                                    if tribunal_elem and len(tribunal_elem) > 0:
                                        result['Tribunal'] = tribunal_elem[0].text.strip()
                                    
                                    # Processo
                                    processo_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblProcesso')]")
                                    if processo_elem and len(processo_elem) > 0:
                                        result['Processo'] = processo_elem[0].text.strip()
                                    
                                    # Data
                                    data_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblData')]")
                                    if data_elem and len(data_elem) > 0:
                                        result['Data'] = data_elem[0].text.strip()
                                    
                                    # Ato
                                    ato_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblAto')]")
                                    if ato_elem and len(ato_elem) > 0:
                                        result['Ato'] = ato_elem[0].text.strip()
                                    
                                    # Descrição
                                    desc_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblDescricao') or contains(@id, 'lblTexto')]")
                                    if desc_elem and len(desc_elem) > 0:
                                        result['Descrição'] = desc_elem[0].text.strip()
                                    
                                    # Interveniente
                                    interv_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblInterveniente')]")
                                    if interv_elem and len(interv_elem) > 0:
                                        result['Interveniente'] = interv_elem[0].text.strip()
                                    
                                    # NIF/NIPC
                                    nif_elem = item.find_elements(By.XPATH, ".//span[contains(@id, 'lblNIF')]")
                                    if nif_elem and len(nif_elem) > 0:
                                        result['NIF/NIPC'] = nif_elem[0].text.strip()
                                    
                                    # Verificar se há links para documentos
                                    links = item.find_elements(By.TAG_NAME, "a")
                                    if links and len(links) > 0:
                                        result['Links'] = []
                                        for link in links:
                                            href = link.get_attribute("href")
                                            if href:
                                                result['Links'].append(href)
                                    
                                    # Se não encontrou campos específicos, extrair todo o texto
                                    if len(result) <= 1:  # Apenas Links ou vazio
                                        all_text = item.text.strip()
                                        if all_text:
                                            result['Conteúdo'] = all_text
                                    
                                    # Só adicionar se tiver algum conteúdo
                                    if result:
                                        results.append(result)
                                except StaleElementReferenceException:
                                    logger.warning(f"Elemento ficou obsoleto durante a extração do item {i}")
                                    continue
                                except Exception as e:
                                    logger.warning(f"Erro ao processar campos do item {i}: {e}")
                                    
                                    # Tentar extrair o texto completo como fallback
                                    try:
                                        all_text = item.text.strip()
                                        if all_text:
                                            results.append({"Conteúdo": all_text})
                                    except:
                                        pass
                                    
                                    continue
                            except Exception as e:
                                logger.warning(f"Erro ao processar item {i}: {e}")
                                continue
                        
                        # Se encontramos resultados na div, retornar
                        if len(results) > 0:
                            return results
                    else:
                        # Se não encontrou itens de resultado, tentar extrair o conteúdo completo da div
                        try:
                            content = results_div[0].text.strip()
                            if content:
                                # Tentar extrair informações do texto completo
                                # Dividir o texto em blocos por padrões comuns
                                blocks = re.split(r'(?:Tribunal:|Processo:|Insolvente:|Credor:|Administrador)', content)
                                if len(blocks) > 1:
                                    # Primeiro bloco geralmente é cabeçalho, ignorar
                                    blocks = blocks[1:]
                                    
                                    # Processar cada bloco
                                    for i, block in enumerate(blocks):
                                        if i >= total_docs:
                                            break
                                            
                                        # Adicionar o prefixo que foi removido no split
                                        if i == 0 or not block.strip().startswith(':'):
                                            block_text = "Tribunal: " + block
                                        elif "Insolvente" in content:
                                            block_text = "Insolvente: " + block
                                        elif "Credor" in content:
                                            block_text = "Credor: " + block
                                        elif "Administrador" in content:
                                            block_text = "Administrador: " + block
                                        else:
                                            block_text = "Processo: " + block
                                            
                                        results.append({"Conteúdo": block_text.strip()})
                                else:
                                    # Se não conseguiu dividir, usar o conteúdo completo
                                    results.append({"Conteúdo": content})
                            
                            if len(results) > 0:
                                return results
                        except Exception as e:
                            logger.warning(f"Erro ao extrair conteúdo da div de resultados: {e}")
                
            except Exception as e:
                logger.warning(f"Erro ao processar div de resultados: {e}")
            
            # Método 3: Extrair texto da página para análise manual
            if len(results) == 0 and total_docs > 0:
                print("Formato de resultados não reconhecido, extraindo texto da página")
                logger.warning("Formato de resultados não reconhecido, extraindo texto da página")
                
                try:
                    # Salvar HTML para análise
                    with open("debug_results_page.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.info("HTML da página de resultados salvo em debug_results_page.html")
                    
                    # Extrair texto da página
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    
                    # Tentar extrair informações do texto completo
                    # Dividir o texto em blocos por padrões comuns
                    blocks = re.split(r'(?:Tribunal:|Processo:|Insolvente:|Credor:|Administrador)', page_text)
                    if len(blocks) > 1:
                        # Primeiro bloco geralmente é cabeçalho, ignorar
                        blocks = blocks[1:]
                        
                        # Processar cada bloco
                        for i, block in enumerate(blocks):
                            if i >= total_docs:
                                break
                                
                            # Adicionar o prefixo que foi removido no split
                            if i == 0 or not block.strip().startswith(':'):
                                block_text = "Tribunal: " + block
                            elif "Insolvente" in page_text:
                                block_text = "Insolvente: " + block
                            elif "Credor" in page_text:
                                block_text = "Credor: " + block
                            elif "Administrador" in page_text:
                                block_text = "Administrador: " + block
                            else:
                                block_text = "Processo: " + block
                                
                            results.append({"Conteúdo": block_text.strip()})
                    else:
                        # Se não conseguiu dividir, usar o conteúdo completo
                        results.append({"Conteúdo": page_text})
                except Exception as e:
                    logger.error(f"Erro ao extrair texto da página: {e}")
                    
                    # Último recurso: adicionar um resultado com informação sobre o erro
                    if len(results) == 0:
                        results.append({
                            "Erro": str(e),
                            "Observação": "Falha na extração de resultados, mas foram encontrados documentos"
                        })
            
            # Verificar se temos pelo menos um resultado
            if len(results) == 0 and total_docs > 0:
                # Adicionar um resultado genérico para cada documento encontrado
                for i in range(total_docs):
                    results.append({
                        "Índice": i + 1,
                        "Total_Documentos": total_docs,
                        "Observação": "Documento detectado mas não foi possível extrair detalhes"
                    })
            
            return results
        except Exception as e:
            print(f"Erro ao extrair resultados: {e}")
            logger.error(f"Erro ao extrair resultados: {e}")
            logger.error(traceback.format_exc())
            
            # Garantir que retornamos algo mesmo em caso de erro
            if total_docs > 0 and len(results) == 0:
                results.append({
                    "Total_Documentos": total_docs,
                    "Data_Extracao": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    "Erro": str(e),
                    "Observação": "Erro durante extração, mas foram encontrados documentos"
                })
            
            return results
    
    def parse_content_to_structured_data(self, content):
        """
        Converte texto não estruturado em dados estruturados
        
        Args:
            content (str): Texto não estruturado
            
        Returns:
            dict: Dicionário com dados estruturados
        """
        result = {}
        
        # Padrões para extração de informações
        patterns = {
            'Tribunal': r'Tribunal:\s*(.*?)(?:\n|$)',
            'Ato': r'Ato:\s*(.*?)(?:\n|$)',
            'Referência': r'Referência:\s*(.*?)(?:\n|$)',
            'Processo': r'Processo:\s*(.*?)(?:\n|$)',
            'Espécie': r'Espécie:\s*(.*?)(?:\n|$)',
            'Data': r'Data:\s*(.*?)(?:\n|$)',
            'Data da propositura da ação': r'Data da propositura da ação:\s*(.*?)(?:\n|$)',
            'Insolvente': r'Insolvente:\s*(.*?)(?:\n|$)',
            'NIF/NIPC': r'NIF/NIPC:\s*(.*?)(?:\n|$)',
            'Administrador Insolvência': r'Administrador Insolvência:\s*(.*?)(?:\n|$)',
        }
        
        # Extrair informações usando os padrões
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                result[key] = match.group(1).strip()
        
        # Extrair credores
        credores = re.findall(r'Credor:\s*(.*?)(?:\n|$)', content)
        if credores:
            result['Credores'] = credores
        
        # Extrair NIFs dos credores
        nifs_credores = re.findall(r'Credor:.*?\nNIF/NIPC:\s*(.*?)(?:\n|$)', content)
        if nifs_credores:
            result['NIFs_Credores'] = nifs_credores
        
        return result
    
    def save_results_to_csv(self, results, output_file="resultados_citius.csv"):
        """
        Salva os resultados em um arquivo CSV
        
        Args:
            results (list): Lista de dicionários com os resultados
            output_file (str): Nome do arquivo de saída
            
        Returns:
            bool: True se os resultados foram salvos com sucesso, False caso contrário
        """
        try:
            if not results:
                print("Nenhum resultado para salvar")
                logger.warning("Nenhum resultado para salvar")
                
                # Criar um arquivo vazio com cabeçalho para indicar que o processo foi executado
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Observação"])
                    writer.writerow(["Nenhum resultado encontrado"])
                
                print(f"Arquivo CSV vazio criado em {output_file}")
                logger.info(f"Arquivo CSV vazio criado em {output_file}")
                return True
            
            print(f"Salvando {len(results)} resultados em {output_file}...")
            
            # Processar resultados para estruturar dados de texto
            processed_results = []
            for result in results:
                if 'Conteúdo' in result and len(result) <= 2:  # Apenas Conteúdo e talvez Links
                    # Tentar extrair dados estruturados do conteúdo
                    structured_data = self.parse_content_to_structured_data(result['Conteúdo'])
                    if structured_data:
                        # Manter Links se existir
                        if 'Links' in result:
                            structured_data['Links'] = result['Links']
                        processed_results.append(structured_data)
                    else:
                        processed_results.append(result)
                else:
                    processed_results.append(result)
            
            # Obter todos os campos únicos de todos os resultados
            all_fields = set()
            for result in processed_results:
                all_fields.update(result.keys())
            
            # Remover campos especiais que não devem ser colunas
            special_fields = ['Links', 'Credores', 'NIFs_Credores']
            for field in special_fields:
                if field in all_fields:
                    all_fields.remove(field)
            
            # Converter para lista e ordenar
            fieldnames = sorted(list(all_fields))
            
            # Adicionar campos especiais no final
            for field in special_fields:
                if any(field in result for result in processed_results):
                    fieldnames.append(field)
            
            # Garantir que o diretório de saída existe
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for result in processed_results:
                    # Tratar campos especiais
                    row = result.copy()
                    
                    # Converter lista de links para string
                    if 'Links' in row and isinstance(row['Links'], list):
                        row['Links'] = '; '.join(row['Links'])
                    
                    # Converter lista de credores para string
                    if 'Credores' in row and isinstance(row['Credores'], list):
                        row['Credores'] = '; '.join(row['Credores'])
                    
                    # Converter lista de NIFs para string
                    if 'NIFs_Credores' in row and isinstance(row['NIFs_Credores'], list):
                        row['NIFs_Credores'] = '; '.join(row['NIFs_Credores'])
                    
                    writer.writerow(row)
            
            print(f"Resultados salvos com sucesso em {output_file}")
            logger.info(f"Resultados salvos com sucesso em {output_file}")
            return True
        except Exception as e:
            print(f"Erro ao salvar resultados em CSV: {e}")
            logger.error(f"Erro ao salvar resultados em CSV: {e}")
            logger.error(traceback.format_exc())
            
            # Tentar salvar em formato simplificado em caso de erro
            try:
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Erro", "Observação"])
                    writer.writerow([str(e), "Erro ao salvar resultados em formato completo"])
                    
                    # Adicionar resultados em formato simplificado
                    for i, result in enumerate(results):
                        writer.writerow([f"Resultado {i+1}", str(result)])
                
                print(f"Resultados salvos em formato simplificado em {output_file}")
                logger.info(f"Resultados salvos em formato simplificado em {output_file}")
                return True
            except Exception as e2:
                print(f"Erro ao salvar resultados em formato simplificado: {e2}")
                logger.error(f"Erro ao salvar resultados em formato simplificado: {e2}")
                return False
    
    def save_results_to_json(self, results, output_file="resultados_citius.json"):
        """
        Salva os resultados em um arquivo JSON
        
        Args:
            results (list): Lista de dicionários com os resultados
            output_file (str): Nome do arquivo de saída
            
        Returns:
            bool: True se os resultados foram salvos com sucesso, False caso contrário
        """
        try:
            if not results:
                print("Nenhum resultado para salvar")
                logger.warning("Nenhum resultado para salvar")
                
                # Criar um arquivo JSON vazio com mensagem
                with open(output_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump({"Observação": "Nenhum resultado encontrado"}, jsonfile, ensure_ascii=False, indent=4)
                
                print(f"Arquivo JSON vazio criado em {output_file}")
                logger.info(f"Arquivo JSON vazio criado em {output_file}")
                return True
            
            print(f"Salvando {len(results)} resultados em {output_file}...")
            
            # Processar resultados para estruturar dados de texto
            processed_results = []
            for result in results:
                if 'Conteúdo' in result and len(result) <= 2:  # Apenas Conteúdo e talvez Links
                    # Tentar extrair dados estruturados do conteúdo
                    structured_data = self.parse_content_to_structured_data(result['Conteúdo'])
                    if structured_data:
                        # Manter Links se existir
                        if 'Links' in result:
                            structured_data['Links'] = result['Links']
                        processed_results.append(structured_data)
                    else:
                        processed_results.append(result)
                else:
                    processed_results.append(result)
            
            # Garantir que o diretório de saída existe
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Converter dados para formato serializável
            serializable_results = []
            for result in processed_results:
                serializable_result = {}
                for key, value in result.items():
                    # Converter tipos não serializáveis
                    if isinstance(value, (datetime.datetime, datetime.date)):
                        serializable_result[key] = value.isoformat()
                    else:
                        serializable_result[key] = value
                serializable_results.append(serializable_result)
            
            with open(output_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(serializable_results, jsonfile, ensure_ascii=False, indent=4)
            
            print(f"Resultados salvos com sucesso em {output_file}")
            logger.info(f"Resultados salvos com sucesso em {output_file}")
            return True
        except Exception as e:
            print(f"Erro ao salvar resultados em JSON: {e}")
            logger.error(f"Erro ao salvar resultados em JSON: {e}")
            logger.error(traceback.format_exc())
            
            # Tentar salvar em formato simplificado em caso de erro
            try:
                with open(output_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump({
                        "Erro": str(e),
                        "Observação": "Erro ao salvar resultados em formato completo",
                        "Resultados_Simplificados": [str(r) for r in results]
                    }, jsonfile, ensure_ascii=False, indent=4)
                
                print(f"Resultados salvos em formato simplificado em {output_file}")
                logger.info(f"Resultados salvos em formato simplificado em {output_file}")
                return True
            except Exception as e2:
                print(f"Erro ao salvar resultados em formato simplificado: {e2}")
                logger.error(f"Erro ao salvar resultados em formato simplificado: {e2}")
                return False
    
    def save_results(self, results, output_base="resultados_citius"):
        """
        Salva os resultados em ambos os formatos CSV e JSON
        
        Args:
            results (list): Lista de dicionários com os resultados
            output_base (str): Nome base do arquivo de saída (sem extensão)
            
        Returns:
            tuple: (bool, bool) indicando sucesso para CSV e JSON respectivamente
        """
        # Remover extensão se fornecida
        output_base = os.path.splitext(output_base)[0]
        
        # Salvar em CSV
        csv_success = self.save_results_to_csv(results, f"{output_base}.csv")
        
        # Salvar em JSON
        json_success = self.save_results_to_json(results, f"{output_base}.json")
        
        return csv_success, json_success
    
    def search(self, nif=None, designacao=None, data_inicio=None, data_fim=None, 
               tribunal=None, grupo_actos=None, acto=None, dias="todos", output_base="resultados_citius"):
        """
        Realiza uma pesquisa completa no Portal Citius
        
        Args:
            nif (str): NIF/NIPC para pesquisa
            designacao (str): Designação para pesquisa
            data_inicio (str): Data de início no formato DD-MM-YYYY
            data_fim (str): Data de fim no formato DD-MM-YYYY
            tribunal (bool): True para "Tribunais Extintos", False para "Nova Estrutura Judiciária"
            grupo_actos (str): Grupo de actos para filtrar
            acto (str): Acto específico para filtrar
            dias (str): Filtro de dias ('15', '30', 'todos')
            output_base (str): Nome base do arquivo de saída (sem extensão)
            
        Returns:
            list: Lista de resultados encontrados
        """
        # Validar parâmetros
        if not nif and not designacao:
            print("É necessário fornecer NIF ou designação para pesquisa")
            logger.error("É necessário fornecer NIF ou designação para pesquisa")
            return []
        
        # Abrir a página de pesquisa
        if not self.open_search_page():
            # Criar arquivos vazios para indicar que o processo foi executado
            self.save_results([], output_base)
            return []
        
        # Preencher o formulário
        if not self.fill_search_form(nif, designacao, data_inicio, data_fim, tribunal, grupo_actos, acto, dias):
            # Criar arquivos vazios para indicar que o processo foi executado
            self.save_results([], output_base)
            return []
        
        # Submeter a pesquisa
        if not self.submit_search():
            # Criar arquivos vazios para indicar que o processo foi executado
            self.save_results([], output_base)
            return []
        
        # Extrair os resultados com timeout para evitar bloqueios
        results = self.extract_results(max_extraction_time=800)
        
        print(f"Total de resultados extraídos: {len(results)}")
        logger.info(f"Total de resultados extraídos: {len(results)}")
        
        # Salvar os resultados automaticamente em ambos os formatos
        self.save_results(results, output_base)
        
        return results

def main():
    """Função principal"""
    # Exibir banner
    print(BANNER)
    
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Web Scraper para o Portal Citius usando Selenium')
    parser.add_argument('--nif', help='NIF/NIPC para pesquisa')
    parser.add_argument('--designacao', help='Designação para pesquisa')
    parser.add_argument('--data-inicio', help='Data de início no formato DD-MM-YYYY')
    parser.add_argument('--data-fim', help='Data de fim no formato DD-MM-YYYY')
    parser.add_argument('--tribunal', choices=['nova', 'extintos'], help='Tipo de tribunal (nova ou extintos)')
    parser.add_argument('--grupo-actos', help='Grupo de actos para filtrar')
    parser.add_argument('--acto', help='Acto específico para filtrar')
    parser.add_argument('--dias', choices=['15', '30', 'todos'], default='todos', help='Filtro de dias (15, 30 ou todos)')
    parser.add_argument('--output', default='resultados_citius', help='Nome base do arquivo de saída (sem extensão)')
    parser.add_argument('--headless', action='store_true', help='Executar em modo headless (sem interface gráfica)')
    parser.add_argument('--debug', action='store_true', help='Ativar modo de debug')
    parser.add_argument('--timeout', type=int, default=60, help='Tempo máximo de espera em segundos para operações')
    parser.add_argument('--man', action='store_true', help='Mostrar manual completo e sair')
    args = parser.parse_args()
    
    if args.man:
        print(MANUAL)
        return 0

    # Validar argumentos
    if not args.nif and not args.designacao:
        print("É necessário fornecer NIF ou designação para pesquisa")
        parser.print_help()
        return 1
    
    # Converter o argumento tribunal para booleano
    tribunal = None
    if args.tribunal:
        tribunal = (args.tribunal == 'extintos')
    
    try:
        # Inicializar o scraper
        scraper = CitiusSeleniumScraper(headless=args.headless, debug=args.debug, timeout=args.timeout)
        
        # Realizar a pesquisa
        results = scraper.search(
            nif=args.nif,
            designacao=args.designacao,
            data_inicio=args.data_inicio,
            data_fim=args.data_fim,
            tribunal=tribunal,
            grupo_actos=args.grupo_actos,
            acto=args.acto,
            dias=args.dias,
            output_base=args.output
        )
        
        if not results:
            print("Nenhum resultado encontrado")
        
        return 0
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        logger.error(f"Erro durante a execução: {e}")
        logger.error(traceback.format_exc())
        
        # Tentar salvar informações de erro
        try:
            error_results = [{
                "Erro": str(e),
                "Data_Extracao": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "Observação": "Erro durante execução do script"
            }]
            
            output_base = args.output
            output_base = os.path.splitext(output_base)[0]
            
            # Salvar informações de erro em CSV
            with open(f"{output_base}.csv", 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["Erro", "Data_Extracao", "Observação"])
                writer.writeheader()
                writer.writerows(error_results)
            
            # Salvar informações de erro em JSON
            with open(f"{output_base}.json", 'w', encoding='utf-8') as jsonfile:
                json.dump(error_results, jsonfile, ensure_ascii=False, indent=4)
            
            print(f"Informações de erro salvas em {output_base}.csv e {output_base}.json")
        except:
            pass
        
        return 1
    finally:
        # Garantir que o WebDriver seja fechado
        if 'scraper' in locals():
            del scraper

if __name__ == "__main__":
    sys.exit(main())
