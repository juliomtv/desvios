import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, session, abort
import io
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_forte_e_aleatoria' # Necessário para sessões (autenticação)
auth = HTTPBasicAuth()

# Usuários para o dashboard
users = {
    "gestao": generate_password_hash("technipfmc")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username
    return None
DATA_FILE = os.path.join(app.root_path, 'data', 'desvios.csv')

# Garante que o arquivo de dados exista com cabeçalhos
def initialize_data_file():
    if not os.path.exists(DATA_FILE):
        # Definindo as colunas para o relatório de desvios
        columns = ['timestamp', 'desvio_tipo', 'descricao']
        df = pd.DataFrame(columns=columns)
        df.to_csv(DATA_FILE, index=False)

initialize_data_file()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Coleta os dados do formulário
        desvio_tipo = request.form.get('desvio_tipo')
        descricao = request.form.get('descricao')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Cria um novo registro
        new_entry = {
            'timestamp': timestamp,
            'desvio_tipo': desvio_tipo,
            'descricao': descricao
        }

        # Adiciona ao CSV
        try:
            df = pd.read_csv(DATA_FILE)
            new_df = pd.DataFrame([new_entry])
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            # Redireciona para evitar reenvio do formulário
            return redirect(url_for('index'))
        except Exception as e:
            # Em caso de erro, pode-se logar ou mostrar uma mensagem
            print(f"Erro ao salvar dados: {e}")
            return render_template('index.html', error="Erro ao registrar o desvio.")

    # Exibe o formulário
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verifica a senha usando a função de verificação
        if username in users and check_password_hash(users.get(username), password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Usuário ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    try:
        df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver vazio, retorna um dashboard sem dados
        return render_template('dashboard.html', data_analysis={'top_desvios': [], 'bottom_desvios': []})

    # Análise de Frequência de Desvios
    if not df.empty:
        # Limpa espaços em branco extras que podem impedir a contagem correta
        df['desvio_tipo'] = df['desvio_tipo'].str.strip()
        frequencia_desvios = df['desvio_tipo'].value_counts()
        
        # Top 5 mais frequentes
        top_desvios = frequencia_desvios.head(5).to_dict()
        
        # Top 5 menos frequentes (excluindo os que já estão no top)
        bottom_desvios_series = frequencia_desvios[~frequencia_desvios.index.isin(top_desvios.keys())].sort_values(ascending=True).head(5)
        bottom_desvios = bottom_desvios_series.to_dict()
        
        # Formata para lista de tuplas para o template
        data_analysis = {
            'top_desvios': list(top_desvios.items()),
            'bottom_desvios': list(bottom_desvios.items())
        }
    else:
        data_analysis = {'top_desvios': [], 'bottom_desvios': []}

    return render_template('dashboard.html', data_analysis=data_analysis)

@app.route('/download')
def download_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Gera o arquivo XLSX
    try:
        df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver vazio, retorna uma mensagem de erro
        return "Nenhum dado para exportar.", 404

    # Cria um buffer de memória para o arquivo Excel
    output = io.BytesIO()
    
    # Escreve o DataFrame no buffer como XLSX
    # Não é possível adicionar senha ao arquivo XLSX diretamente com pandas/openpyxl
    # A proteção é feita pela rota de login
    df.to_excel(output, index=False, sheet_name='Relatorio_Desvios', engine='openpyxl')
    output.seek(0)
    
    # Envia o arquivo
    return send_file(output, as_attachment=True, download_name='relatorio_desvios.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    # Para rodar em produção, use um servidor WSGI como Gunicorn
    # Para o propósito de entrega do código, deixamos o modo debug
    app.run(debug=True, host='0.0.0.0', port=5000)
