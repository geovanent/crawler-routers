from app import app
from flask import request
from pathlib import Path
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

class Chrome(webdriver.Chrome):
    def __init__(self, *args, **kwargs):        
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Não exibir o navegador
        options.add_experimental_option(
            "prefs", {
                'download.default_directory' : str(Path().absolute()),
            }
        )

        super().__init__(options=options)
    
    def wait_until(self, method, timeout=10, interval=1):
        return WebDriverWait(self, timeout, interval).until(method)
    
    def element(self, locator):
        return self.find_element(*locator)

        
def ID(value):
    return By.ID, value

def name(value):
    return By.NAME, value

def css(value):
    return By.CSS_SELECTOR, value

def xpath(value):
    return By.XPATH, value

def link_contains(value):
    return By.PARTIAL_LINK_TEXT, value
    

present = EC.presence_of_element_located
invisible = EC.invisibility_of_element_located


def js_href(el):
    return el.get_attribute('href').partition(':')[-1]

class Crawler:
    URL = 'https://nfse.salvador.ba.gov.br/'  
    
    def __init__(self, driver):
        self.driver = driver    
    
    def login(self, login, senha, cpf):
        # 1. Acessa o site.
        self.driver.get(self.URL)

        # 2. Preenche os dados de login do cliente
        el = self.driver.element
        el(ID('txtLogin')).send_keys(login)
        el(ID('txtSenha')).send_keys(senha)
        # Clica no botão de login
        el(name('cmdLogin')).click()

        # Esse cliente aparecer um link para clicar em acessar
        if(login == '11392814000135'):
            el(link_contains('Acessar Nota Salvador')).click()

        # Vai para a tela de emissão de notas
        el(link_contains('Emissão NFS-e')).click()
        
        # Mostra os clientes cadastrados no console (vai ser retornado na api depois)
        items_select = self.driver.find_element_by_id('ddlApelido')
        print(items_select.text)

        #caso o cliente estiver cadastrado selecionar o mesmo
        apelido = False
        if(apelido):
            el = self.driver.find_element_by_id('ddlApelido')
            for option in el.find_elements_by_tag_name('option'):
                if option.text == 'BASE MEDICAL':
                    option.click() # select() in earlier versions of webdriver
                    break
        
        # dados do cliente
        self.driver.find_element_by_id('tbCPFCNPJTomador').send_keys(cpf)
        
        # Clica em avançar
        self.driver.find_element_by_id('btAvancar').click()


        return 'tudo certo ate aqui'
    


@app.route('/crawlar', methods=['POST'])
def crawlar():
    #recebe os dados enviado pelo post e distribui nos campos
    req_data = request.get_json(force=True)
    login = req_data['login']
    senha = req_data['senha']
    cpf = req_data['cliente']['cpf']

    crawlinho = Crawler(Chrome())
    res = crawlinho.login(login, senha, cpf)
    return 'usando login: {} e senha {}'.format(login, senha)