# 📄 Citius Selenium Scraper

Script em Python que automatiza a recolha de informações públicas do [Portal Citius](https://www.citius.mj.pt/) através de web scraping com Selenium WebDriver.

---

## 📌 Funcionalidades

- Pesquisa por **NIF/NIPC** ou **designação**
- Filtro por datas, tipo de tribunal, grupo de actos e acto específico
- Extração de resultados para **CSV** e/ou **JSON**
- Modo **headless** para execução em background
- Geração de logs e tratamento de erros automático

---

## ⚙️ Requisitos

- Python **3.6+**
- Google Chrome ou Chromium instalado
- Dependências Python (ver `requirements.txt`)

---

## 📦 Instalação

1. Clona o repositório:

```bash
git clone https://github.com/Raam977/citius-selenium-scraper.git
cd citius-selenium-scraper
```

2. Instala as dependências: 

```bash
pip install -r requirements.txt`
```


---

## 🚀 Utilização


```bash
python citius_selenium_scraper.py [opções]
```


### 🔧 Exemplos:

```bash
# Pesquisa por NIF
python citius_selenium_scraper.py --nif 12345678

# Pesquisa por designação com datas
python citius_selenium_scraper.py --designacao "Empresa XYZ" --data-inicio "01-01-2025" --data-fim "31-01-2025"

# Execução completa em modo headless
python citius_selenium_scraper.py --nif 123456780 --dias todos --output resultados_citius --headless
```

---

## 🔍 Opções disponíveis

|Argumento|Descrição|
|---|---|
|`--nif`|NIF/NIPC a pesquisar|
|`--designacao`|Designação (nome) da entidade|
|`--data-inicio`|Data de início no formato `DD-MM-YYYY`|
|`--data-fim`|Data de fim no formato `DD-MM-YYYY`|
|`--tribunal`|`nova` ou `extintos`|
|`--grupo-actos`|Grupo de actos a filtrar|
|`--acto`|Acto específico|
|`--dias`|`15`, `30` ou `todos` (padrão: `todos`)|
|`--output`|Nome base do ficheiro de saída (sem extensão)|
|`--headless`|Executar sem interface gráfica|
|`--debug`|Mostrar logs detalhados|
|`--timeout`|Tempo máximo de espera (em segundos)|
|`--man`|Mostrar manual completo|
|`-h, --help`|Mostrar ajuda resumida|

---

## 📁 Output

Os resultados são guardados automaticamente em:

- `resultados_citius.csv`
    
- `resultados_citius.json`
    

Podes personalizar o nome com `--output`.

---

## 🐛 Logs e depuração

- Log completo em `citius_scraper.log`
    
- Usa `--debug` para ativar logs detalhados
    
- Em caso de erro, um ficheiro `debug_results_page.html` pode ser gerado

---

## ⚠️ Avisos

- Este script simula interação de utilizador, respeitando os limites técnicos do Portal Citius.
    
- Usa com responsabilidade e evita execuções em massa.
    
- Não ultrapasses os termos de utilização do portal.
    

---

## 📄 Licença

Distribuído para fins educacionais e uso legítimo. Consulta os termos de uso do Portal Citius.

---

## Limitações

- O site pode mudar sua estrutura HTML, exigindo atualizações no parser
- Pesquisas muito amplas podem retornar muitos resultados e demorar mais tempo
- O site pode implementar limitações de taxa de requisições no futuro

---

## Contribuições


Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.


