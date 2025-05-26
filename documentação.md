# Citius Selenium Scraper

Este script permite automatizar a pesquisa e recolha de processos no Portal Citius utilizando o Selenium WebDriver para preencher formulários e extrair dados.

## Funcionalidades

- Pesquisa por NIF/NIPC ou designação
- Definição de intervalo de datas (início e fim)
- Seleção de tipo de tribunal (Nova Estrutura Judiciária ou Tribunais Extintos)
- Filtro por grupo de atos e atos específicos
- Filtro por período de dias (15, 30 ou todos)
- **Exportação automática** dos resultados em formatos CSV e JSON
- **Mecanismo de timeout** para evitar bloqueios durante a extração
- **Extração robusta** que garante resultados mesmo em caso de falhas parciais

## Pré-requisitos

- Python 3.6 ou superior
- Google Chrome ou Chromium Browser
- Bibliotecas Python: selenium, webdriver-manager

## Instalação

1. Instale as dependências necessárias:

```bash
pip install selenium webdriver-manager
```

2. Certifique-se de que o Chrome ou Chromium está instalado no seu sistema.

## Utilização

### Linha de Comando

O script pode ser executado a partir da linha de comando com vários parâmetros:

```bash
python citius_selenium_scraper.py --nif 12345678 --data-inicio "18-05-2025" --data-fim "24-05-2025" --dias todos --output resultados
```

### Parâmetros Disponíveis

- `--nif`: NIF/NIPC para pesquisa
- `--designacao`: Designação para pesquisa (alternativa ao NIF)
- `--data-inicio`: Data de início no formato DD-MM-YYYY
- `--data-fim`: Data de fim no formato DD-MM-YYYY
- `--tribunal`: Tipo de tribunal (opções: 'nova' ou 'extintos')
- `--grupo-actos`: Grupo de actos para filtrar
- `--acto`: Acto específico para filtrar
- `--dias`: Filtro de dias (opções: '15', '30', 'todos', padrão: 'todos')
- `--output`: Nome base do arquivo de saída (sem extensão, padrão: 'resultados_citius')
- `--headless`: Executar em modo headless (sem interface gráfica)
- `--debug`: Ativar modo de debug com logs detalhados
- `--timeout`: Tempo máximo de espera em segundos para operações (padrão: 60)

### Exemplos de Uso

1. Pesquisa básica por NIF:

```bash
python citius_selenium_scraper.py --nif 515755230
```

2. Pesquisa por designação com intervalo de datas:

```bash
python citius_selenium_scraper.py --designacao "Empresa XYZ" --data-inicio "01-01-2025" --data-fim "31-01-2025"
```

3. Pesquisa completa com todos os filtros:

```bash
python citius_selenium_scraper.py --nif 12345678 --data-inicio "18-05-2025" --data-fim "24-05-2025" --tribunal nova --dias todos --output resultados_completos --headless
```

4. Pesquisa com timeout personalizado para sites lentos:

```bash
python citius_selenium_scraper.py --nif 12345678 --timeout 120
```

## Exportação Automática

O script agora exporta automaticamente os resultados em **ambos os formatos CSV e JSON** após cada pesquisa bem-sucedida:

- Se especificar `--output resultados`, serão gerados:
  - `resultados.csv`
  - `resultados.json`

Não é necessário especificar o formato, pois ambos são gerados automaticamente.

## Mecanismo de Timeout e Extração Robusta

O script inclui mecanismos avançados para garantir que os resultados sejam sempre extraídos e salvos:

- **Timeout de extração**: Limita o tempo máximo de processamento para evitar bloqueios
- **Extração em múltiplas etapas**: Tenta diferentes métodos de extração em caso de falha
- **Fallback para resultados parciais**: Mesmo que a extração detalhada falhe, salva informações básicas
- **Tratamento de erros robusto**: Garante que os arquivos de saída sejam sempre criados, mesmo em caso de erro

## Estrutura do Código

O script está organizado em uma classe principal `CitiusSeleniumScraper` que contém os seguintes métodos principais:

- `__init__`: Inicializa o WebDriver e configurações
- `open_search_page`: Abre a página de pesquisa do Portal Citius
- `fill_search_form`: Preenche o formulário de pesquisa com os parâmetros fornecidos
- `submit_search`: Submete o formulário de pesquisa
- `extract_results`: Extrai os resultados da página com mecanismo de timeout
- `save_results_to_csv`: Salva os resultados em um arquivo CSV
- `save_results_to_json`: Salva os resultados em um arquivo JSON
- `save_results`: Salva os resultados em ambos os formatos
- `search`: Método principal que coordena todo o processo de pesquisa

## Resolução de Problemas

### Extração Incompleta ou Timeout

Se a extração estiver incompleta ou atingir o timeout:

1. Aumente o valor do parâmetro `--timeout` (ex: `--timeout 120`)
2. Execute sem o modo headless para visualizar o processo
3. Verifique se o Portal Citius está respondendo normalmente
4. Os resultados parciais serão salvos mesmo em caso de timeout

### Ficheiros de Resultados Vazios

Se os ficheiros de resultados estiverem vazios:

1. Verifique se o script encontrou resultados (mensagem "Total de documentos encontrados: X")
2. Verifique se há erros nos logs relacionados à extração de dados
3. Tente executar sem o modo headless para visualizar o processo
4. Verifique se o Portal Citius alterou a estrutura da página de resultados

### Erro de Versão do ChromeDriver

Se encontrar erros relacionados à incompatibilidade entre o ChromeDriver e o Chrome, o script tentará automaticamente:

1. Detectar a versão do Chrome/Chromium instalada
2. Usar o driver local se disponível

Se o problema persistir, você pode:

- Atualizar o Chrome/Chromium para a versão mais recente
- Instalar manualmente o ChromeDriver compatível com sua versão do Chrome
- Modificar o script para usar outro navegador (Firefox/GeckoDriver)

### Página Não Carrega

Se a página do Portal Citius não carregar corretamente:

1. Verifique sua conexão com a internet
2. Certifique-se de que o Portal Citius está acessível
3. Tente executar sem o modo headless para depuração visual
4. Aumente os tempos de espera no código se necessário

## Logs e Depuração

O script gera logs detalhados em:

1. Console (saída padrão)
2. Arquivo `citius_scraper.log`

Para depuração avançada, use o parâmetro `--debug` para obter logs mais detalhados.

## Limitações

- O script depende da estrutura atual do Portal Citius. Alterações no site podem exigir atualizações no código.
- Algumas operações podem ser bloqueadas por CAPTCHA ou outras medidas de segurança.
- O desempenho pode variar dependendo da velocidade da conexão e da carga do servidor.

## Personalização

Para personalizar o script para suas necessidades específicas, você pode modificar:

- Os seletores CSS/XPath se a estrutura do site mudar
- Os tempos de espera para ajustar a diferentes velocidades de conexão
- Os formatos de saída para incluir campos adicionais

## Notas Adicionais

- Este script foi desenvolvido para fins educacionais e de automação legítima.
- Respeite os termos de serviço do Portal Citius e evite sobrecarregar o servidor com muitas requisições.
- Considere adicionar atrasos entre as requisições para evitar bloqueios.
