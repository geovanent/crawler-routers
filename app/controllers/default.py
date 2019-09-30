from app import app
from flask import request

#Alguns testes de rota no flesk (não necessario para o projeto)
@app.route('/')
def index():
    return 'Inicio'

@app.route('/getNotas')
@app.route('/getNotas/<name>')
def getNotas(name=None):
    return "ops, %s" % name

@app.route('/enviaNota', methods=['POST'])
def enviaNota():
    req_data = request.get_json(force=True)
    login = req_data['login']
    senha = req_data['senha']
    return 'valor do login e: {} e senha {}'.format(login, senha)