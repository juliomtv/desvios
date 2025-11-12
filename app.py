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
DATA_FILE_HB3 = os.path.join(app.root_path, 'data', 'desvios_hb3.csv')
DATA_FILE_HB1HB2 = os.path.join(app.root_path, 'data', 'desvios_hb1hb2.csv')

def get_data_file(galpao):
    if galpao == 'HB3':
        return DATA_FILE_HB3
    elif galpao == 'HB1/HB2':
        return DATA_FILE_HB1HB2
    return None

# Garante que o arquivo de dados exista com cabeçalhos
def initialize_data_file(data_file):
    if not os.path.exists(data_file):
        # Definindo as colunas para o relatório de desvios
        # Adicionando a coluna 'galpao' para garantir a consistência, embora o arquivo já seja separado
        columns = ['timestamp', 'desvio_tipo', 'descricao', 'galpao']
        df = pd.DataFrame(columns=columns)
        df.to_csv(data_file, index=False, sep=';')

# Inicializa os dois arquivos de dados
initialize_data_file(DATA_FILE_HB3)
initialize_data_file(DATA_FILE_HB1HB2)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Coleta os dados do formulário
        desvio_tipo = request.form.get('desvio_tipo')
        descricao = request.form.get('descricao')
        galpao = request.form.get('galpao') # Novo campo para o galpão
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not galpao:
            return render_template('index.html', error="Selecione o galpão para o desvio.")

        data_file = get_data_file(galpao)
        if not data_file:
            return render_template('index.html', error="Galpão inválido selecionado.")

        # Cria um novo registro
        new_entry = {
            'timestamp': timestamp,
            'desvio_tipo': desvio_tipo,
            'descricao': descricao,
            'galpao': galpao # Adiciona o galpão ao registro
        }

        # Adiciona ao CSV
        try:
            # Garante que o diretório 'data' exista
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            
            # Garante que o arquivo exista com o cabeçalho correto
            initialize_data_file(data_file)

            df = pd.read_csv(data_file, sep=';')
            new_df = pd.DataFrame([new_entry])
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(data_file, index=False, sep=';')
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
        galpao_login = request.form.get('galpao_login') # Novo campo para o galpão no login

        if username in users and check_password_hash(users.get(username), password):
            if galpao_login in ['HB3', 'HB1/HB2']:
                session['logged_in'] = True
                session['galpao_acesso'] = galpao_login # Salva o galpão de acesso na sessão
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Selecione o galpão para acesso.')
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
    
    galpao_acesso = session.get('galpao_acesso')
    data_file = get_data_file(galpao_acesso)

    if not data_file:
        # Isso não deve acontecer se o login for bem-sucedido, mas é uma segurança
        session.pop('logged_in', None)
        return redirect(url_for('login'))

    try:
        df = pd.read_csv(data_file, sep=';')
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver vazio, retorna um dashboard sem dados
        return render_template('dashboard.html', galpao=galpao_acesso, data_analysis={'top_desvios': [], 'bottom_desvios': []})

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

    return render_template('dashboard.html', galpao=galpao_acesso, data_analysis=data_analysis)

@app.route('/download')
def download_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    galpao_acesso = session.get('galpao_acesso')
    data_file = get_data_file(galpao_acesso)

    if not data_file:
        return "Erro: Galpão de acesso não definido na sessão.", 400

    # Gera o arquivo XLSX
    try:
        df = pd.read_csv(data_file, sep=';')
    except pd.errors.EmptyDataError:
        # Se o arquivo estiver vazio, retorna uma mensagem de erro
        return "Nenhum dado para exportar.", 404

    # Cria um buffer de memória para o arquivo Excel
    output = io.BytesIO()
    
    # Escreve o DataFrame no buffer como XLSX
    # Não é possível adicionar senha ao arquivo XLSX diretamente com pandas/openpyxl
    # A proteção é feita pela rota de login
    df.to_excel(output, index=False, sheet_name=f'Relatorio_Desvios_{galpao_acesso.replace("/", "_")}', engine='openpyxl')
    output.seek(0)
    
    # Envia o arquivo
    download_name = f'relatorio_desvios_{galpao_acesso.replace("/", "_")}.xlsx'
    return send_file(output, as_attachment=True, download_name=download_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    # Para rodar em produção, use um servidor WSGI como Gunicorn
    # Para o propósito de entrega do código, deixamos o modo debug
    app.run(debug=True, host='0.0.0.0', port=5000)
