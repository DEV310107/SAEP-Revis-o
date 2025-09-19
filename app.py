# ================================================================================
# SISTEMA DE GERENCIAMENTO DE AUTOPEÇAS - FLASK APPLICATION
# ================================================================================
# 
# Este é o arquivo principal do sistema de autopeças desenvolvido em Flask.
# 
# FUNCIONALIDADES PRINCIPAIS:
# - Sistema de autenticação de usuários
# - Cadastro, edição e exclusão de autopeças (CRUD)
# - Controle de estoque com alertas de estoque baixo
# - Interface web responsiva com templates HTML
# 
# DEPENDÊNCIAS NECESSÁRIAS:
# - Flask: Framework web para Python
# - PyMySQL: Conector para banco de dados MySQL
# - datetime: Para manipulação de datas (padrão do Python)
# 
# ESTRUTURA DO BANCO DE DADOS:
# - Tabela 'usuarios': ID_USUARIO, EMAIL, SENHA, NOME_COMPLETO
# - Tabela 'autopecas': ID_PECA, NOME_PECA, NUM_SERIAL, ESTOQUE, ESTOQUE_MINIMO, PRECO, DESCRICAO
# 
# INSTALAÇÃO DAS DEPENDÊNCIAS:
# pip install flask pymysql
# 
# COMO EXECUTAR:
# python app.py
# Acessar: http://localhost:5000
# ================================================================================

# IMPORTAÇÕES
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql                # Biblioteca para conectar com MySQL
from datetime import datetime # Para trabalhar com datas e horários

# INICIALIZAÇÃO DA APLICAÇÃO FLASK
app = Flask(__name__)

# CHAVE SECRETA
# Necessária para criptografar sessões e cookies
# EM PRODUÇÃO: Use uma chave mais complexa e armazene em variável de ambiente
app.secret_key = 'chave_secreta_saep_2025'

# CONFIGURAÇÃO DA CONEXÃO COM O BANCO DE DADOS
# 
# Parâmetros para conectar com MySQL local (XAMPP)
# Ajuste conforme sua configuração:
# - host: endereço do servidor MySQL
# - port: porta do MySQL (padrão 3306)
# - user: usuário do banco (padrão 'root' no XAMPP)
# - password: senha (vazio por padrão no XAMPP)
# - database: nome do banco criado
# - charset: codificação para suportar acentos
# - autocommit: confirma automaticamente as transações
DB_CONFIG = {
    'host': '127.0.0.1',        # Localhost
    'port': 3306,               # Porta padrão MySQL
    'user': 'root',             # Usuário padrão XAMPP
    'password': '',             # Senha vazia (padrão XAMPP)
    'database': 'SAEB_DB',      # Nome do banco criado
    'charset': 'utf8mb4',       # Suporte completo UTF-8
    'autocommit': True          # Auto-confirma transações
}

# ================================================================================
# FUNÇÃO DE CONEXÃO COM O BANCO DE DADOS
# ================================================================================

def get_db_connection():
    """
    Estabelece conexão com o banco de dados MySQL.
    
    Esta função centraliza a lógica de conexão, facilitando manutenção e debug.
    
    Returns:
        pymysql.Connection: Objeto de conexão se bem-sucedida
        None: Se houver erro na conexão
    
    Tratamento de erros:
        - pymysql.Error: Erros específicos do MySQL (credenciais, rede, etc.)
        - Exception: Outros erros gerais
    
    Como usar:
        conn = get_db_connection()
        if conn:
            # usar a conexão
            conn.close()
    """
    try:
        print("Tentando conectar ao banco de dados...")
        
        # **DB_CONFIG desempacota o dicionário como parâmetros nomeados
        connection = pymysql.connect(**DB_CONFIG)
        
        print("Conexão bem-sucedida!")
        return connection
        
    except pymysql.Error as e:
        # Erros específicos do MySQL (banco não existe, credenciais inválidas, etc.)
        print(f'Erro MySQL: {e}')
        flash(f'Erro ao conectar com o banco de dados MySQL: {e}', 'error')
        return None
        
    except Exception as e:
        # Outros erros gerais (rede, firewall, etc.)
        print(f'Erro geral: {e}')
        flash(f'Erro geral ao conectar: {e}', 'error')
        return None

# ================================================================================
# ROTAS DA APLICAÇÃO
# ================================================================================

@app.route('/')
def index():
    """
    ROTA INICIAL (/)
    
    Redireciona usuários para a página apropriada:
    - Se já está logado → Dashboard
    - Se não está logado → Login
    
    Verifica se existe 'user_id' na sessão Flask.
    Sessão persiste dados entre requisições do mesmo usuário.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    ROTA DE AUTENTICAÇÃO (/login)
    
    Métodos aceitos: GET e POST
    - GET: Exibe formulário de login
    - POST: Processa credenciais enviadas
    
    Processo de autenticação:
    1. Recebe email e senha do formulário
    2. Busca usuário no banco de dados
    3. Verifica se credenciais coincidem
    4. Se válidas: cria sessão e redireciona para dashboard
    5. Se inválidas: exibe mensagem de erro
    """
    if request.method == 'POST':
        # Obtém dados do formulário HTML
        email = request.form['email']    # Campo name="email" do HTML
        senha = request.form['senha']    # Campo name="senha" do HTML
        
        # Tenta estabelecer conexão com banco
        conn = get_db_connection()
        if conn:
            try:
                # Cria cursor que retorna resultados como dicionários
                # DictCursor permite acessar campos por nome: user['EMAIL']
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # CONSULTA SQL SEGURA usando parâmetros (%s)
                # Previne SQL Injection - NUNCA concatenar strings diretamente!
                # Busca usuário com email E senha exatos
                cursor.execute("SELECT * FROM usuario WHERE EMAIL = %s AND SENHA = %s", (email, senha))
                
                # fetchone() retorna apenas 1 resultado (ou None se não encontrar)
                user = cursor.fetchone()
                
                if user:
                    # AUTENTICAÇÃO BEM-SUCEDIDA
                    # Armazena dados do usuário na sessão Flask
                    # session[] persiste entre requisições do mesmo usuário
                    session['user_id'] = user['ID_USUARIO']    # ID para queries futuras
                    session['user_name'] = user['NOME']        # Nome para exibição
                    
                    # Redireciona para dashboard após login
                    return redirect(url_for('dashboard'))
                else:
                    # CREDENCIAIS INVÁLIDAS
                    # flash() cria mensagem temporária para próxima página
                    # Categoria 'error' define cor/estilo da mensagem
                    flash('Credenciais inválidas. Tente novamente.', 'error')
                    
            except pymysql.Error as e:
                flash(f'Erro ao verificar credenciais: {e}', 'error')
            finally:
                # SEMPRE fechar cursor e conexão para liberar recursos
                cursor.close()
                conn.close()
    
    # Se chegou aqui: método GET ou login falhou
    # Renderiza template login.html com formulário
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    ROTA DE LOGOUT (/logout)
    
    Encerra a sessão do usuário e redireciona para login.
    
    Processo:
    1. session.clear() remove TODOS os dados da sessão
    2. Redireciona para página de login
    3. Usuário precisará fazer login novamente
    
    Segurança: Sempre limpar sessão ao fazer logout
    """
    # Remove todos os dados da sessão (user_id, user_name, etc.)
    session.clear()
    
    # Redireciona para página de login
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """
    ROTA DO DASHBOARD (/dashboard)
    
    Página principal após login bem-sucedido.
    Apresenta resumo do sistema e links de navegação.
    
    Proteção: Verifica se usuário está logado
    """
    # VERIFICAÇÃO DE AUTENTICAÇÃO
    # Se não existe 'user_id' na sessão = usuário não logado
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Renderiza template do dashboard
    # Pode passar dados do contexto: render_template('dashboard.html', dados=valor)
    return render_template('dashboard.html')

@app.route('/autopecas')
def autopecas():
    """
    ROTA DE GERENCIAMENTO DE AUTOPEÇAS (/autopecas)
    
    Funcionalidades:
    - Lista todas as autopeças cadastradas
    - Permite busca por nome ou número de série
    - Exibe status do estoque (OK/Baixo)
    - Fornece links para editar/excluir
    
    Parâmetros GET opcionais:
    - search: termo de busca para filtrar resultados
    """
    # VERIFICAÇÃO DE AUTENTICAÇÃO (padrão em todas as rotas protegidas)
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # CAPTURA PARÂMETRO DE BUSCA
    # request.args.get('search', '') pega parâmetro da URL
    # Exemplo: /autopecas?search=filtro → search = 'filtro'
    # Valor padrão: string vazia se não fornecido
    search = request.args.get('search', '')
    
    # Inicializa conexão e lista de resultados
    conn = get_db_connection()
    autopecas_list = []  # Lista vazia caso haja erro na conexão
    
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # LÓGICA DE BUSCA CONDICIONAL
            if search:
                # BUSCA COM FILTRO
                # LIKE %termo% busca em qualquer parte do texto
                # Busca tanto no nome da peça quanto no número serial
                cursor.execute("""
                    SELECT * FROM autopeca 
                    WHERE NOME_PECA LIKE %s OR NUM_SERIAL LIKE %s 
                    ORDER BY NOME_PECA
                """, (f'%{search}%', f'%{search}%'))
            else:
                # LISTAR TODAS (sem filtro)
                # Ordena por nome para facilitar localização
                cursor.execute("SELECT * FROM autopeca ORDER BY NOME_PECA")
            
            # fetchall() retorna TODAS as linhas encontradas
            # Cada linha é um dicionário (devido ao DictCursor)
            autopecas_list = cursor.fetchall()
            
        except pymysql.Error as e:
            flash(f'Erro ao buscar autopeças: {e}', 'error')
        finally:
            # SEMPRE fechar recursos
            cursor.close()
            conn.close()
    
    # RENDERIZA TEMPLATE COM DADOS
    # autopecas=autopecas_list: passa dados para o template HTML
    # search=search: mantém termo de busca no campo (UX)
    return render_template('autopecas.html', autopecas=autopecas_list, search=search)

@app.route('/autopecas/add', methods=['POST'])
def add_autopeca():
    """
    ROTA PARA ADICIONAR NOVA AUTOPEÇA (/autopecas/add)
    
    Método: POST (dados enviados pelo formulário HTML)
    
    Processo:
    1. Recebe dados do formulário
    2. Valida informações básicas
    3. Insere no banco de dados
    4. Redireciona com mensagem de sucesso/erro
    
    Campos obrigatórios: nome_peca, num_serie, estoque, estoque_minimo, preco
    Campos opcionais: descricao, compatibilidade
    """
    # Verificação de autenticação
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # CAPTURA DADOS DO FORMULÁRIO
    # request.form[] acessa campos enviados via POST
    # Correspondem aos atributos name="" dos inputs HTML
    nome_peca = request.form['nome_peca']
    descricao = request.form['descricao']
    num_serie = request.form['num_serie']
    compatibilidade = request.form['compatibilidade']
    
    # CONVERSÃO DE TIPOS
    # Campos numéricos vêm como string, precisam ser convertidos
    try:
        estoque = int(request.form['estoque'])
        estoque_minimo = int(request.form['estoque_minimo'])
        preco = float(request.form['preco'])
    except ValueError:
        flash('Valores numéricos inválidos. Verifique estoque e preço.', 'error')
        return redirect(url_for('autopecas'))
    
    # VALIDAÇÕES DE NEGÓCIO
    # Regras de negócio para garantir consistência dos dados
    if estoque < 0:
        flash('Estoque não pode ser negativo', 'error')
        return redirect(url_for('autopecas'))
    
    if estoque_minimo < 0:
        flash('Estoque mínimo não pode ser negativo', 'error')
        return redirect(url_for('autopecas'))
        
    if preco <= 0:
        flash('Preço deve ser maior que zero', 'error')
        return redirect(url_for('autopecas'))
    
    # INSERÇÃO NO BANCO DE DADOS
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # SQL INSERT com campos nomeados para clareza
            # %s são placeholders que previnem SQL Injection
            cursor.execute("""
                INSERT INTO autopeca (NOME_PECA, DESCRICAO, ESTOQUE, ESTOQUE_MINIMO, 
                                     NUM_SERIAL, COMPATIBILIDADE, PRECO)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nome_peca, descricao, estoque, estoque_minimo, num_serie, compatibilidade, preco))
            
            # commit() confirma a transação no banco
            # Sem commit(), dados não são salvos permanentemente
            conn.commit()
            
            flash('Autopeça adicionada com sucesso!', 'success')
            
        except pymysql.Error as e:
            # Trata erros específicos do MySQL (duplicata, constraint, etc.)
            flash(f'Erro ao adicionar autopeça: {e}', 'error')
        finally:
            # SEMPRE executar, mesmo com erro
            cursor.close()
            conn.close()
    
    # Redireciona de volta para listagem (padrão POST-Redirect-GET)
    return redirect(url_for('autopecas'))

@app.route('/autopecas/edit/<int:id>')
def edit_autopeca(id):
    """
    ROTA PARA EXIBIR FORMULÁRIO DE EDIÇÃO (/autopecas/edit/<id>)
    
    Parâmetro da URL:
    - <int:id>: Flask automaticamente converte para integer
    - Corresponde ao ID_PECA da autopeça a ser editada
    
    Processo:
    1. Busca autopeça pelo ID
    2. Se encontrada: renderiza formulário pré-preenchido
    3. Se não encontrada: redireciona com erro
    """
    # Verificação de autenticação
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Inicializa variável para armazenar dados da peça
    autopeca = None
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Busca autopeça específica pelo ID
            # (id,) - tupla com um elemento (vírgula necessária!)
            cursor.execute("SELECT * FROM autopeca WHERE ID_PECA = %s", (id,))
            autopeca = cursor.fetchone()  # Retorna dict ou None
            
        except pymysql.Error as e:
            flash(f'Erro ao buscar autopeça: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    # VERIFICAÇÃO SE AUTOPEÇA EXISTE
    if not autopeca:
        flash('Autopeça não encontrada!', 'error')
        return redirect(url_for('autopecas'))
    
    # Renderiza formulário de edição com dados pré-preenchidos
    # autopeca=autopeca passa dict com dados para o template
    return render_template('edit_autopeca.html', autopeca=autopeca)

@app.route('/autopecas/update/<int:id>', methods=['POST'])
def update_autopeca(id):
    """
    ROTA PARA PROCESSAR ATUALIZAÇÃO DE AUTOPEÇA (/autopecas/update/<id>)
    
    Método: POST (dados do formulário de edição)
    Parâmetro: <int:id> - ID da autopeça a ser atualizada
    
    Processo similar ao ADD, mas usa UPDATE SQL ao invés de INSERT
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # CAPTURA E CONVERSÃO DOS DADOS (igual ao add_autopeca)
    nome_peca = request.form['nome_peca']
    descricao = request.form['descricao']
    num_serie = request.form['num_serie']
    compatibilidade = request.form['compatibilidade']
    
    try:
        estoque = int(request.form['estoque'])
        estoque_minimo = int(request.form['estoque_minimo'])
        preco = float(request.form['preco'])
    except ValueError:
        flash('Valores numéricos inválidos!', 'error')
        return redirect(url_for('edit_autopeca', id=id))
    
    # VALIDAÇÕES (com redirecionamento para formulário de edição)
    if estoque < 0:
        flash('Estoque não pode ser negativo', 'error')
        return redirect(url_for('edit_autopeca', id=id))
    
    if estoque_minimo < 0:
        flash('Estoque mínimo não pode ser negativo', 'error')
        return redirect(url_for('edit_autopeca', id=id))
        
    if preco <= 0:
        flash('Preço deve ser maior que zero', 'error')
        return redirect(url_for('edit_autopeca', id=id))
    
    # ATUALIZAÇÃO NO BANCO
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # SQL UPDATE - atualiza registro específico usando WHERE
            # Todos os campos são atualizados, mesmo que não tenham mudado
            cursor.execute("""
                UPDATE autopeca 
                SET NOME_PECA=%s, DESCRICAO=%s, ESTOQUE=%s, ESTOQUE_MINIMO=%s, 
                    NUM_SERIAL=%s, COMPATIBILIDADE=%s, PRECO=%s
                WHERE ID_PECA=%s
            """, (nome_peca, descricao, estoque, estoque_minimo, num_serie, compatibilidade, preco, id))
            
            conn.commit()
            flash('Autopeça atualizada com sucesso!', 'success')
            
        except pymysql.Error as e:
            flash(f'Erro ao atualizar autopeça: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    # Volta para listagem após atualização
    return redirect(url_for('autopecas'))

@app.route('/autopecas/delete/<int:id>')
def delete_autopeca(id):
    """
    ROTA PARA EXCLUIR AUTOPEÇA (/autopecas/delete/<id>)
    
    Método: GET (chamada direta via link)
    Parâmetro: <int:id> - ID da autopeça a ser excluída
    
    ATENÇÃO: Em produção, use POST para operações destrutivas!
    Aqui usa GET por simplicidade didática.
    
    Processo:
    1. Confirma autenticação
    2. Executa DELETE no banco
    3. Redireciona com feedback
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # EXCLUSÃO NO BANCO
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # SQL DELETE - remove registro específico
            # CUIDADO: Não há confirmação adicional aqui!
            # A confirmação JavaScript está no template HTML
            cursor.execute("DELETE FROM autopeca WHERE ID_PECA = %s", (id,))
            
            conn.commit()
            flash('Autopeça excluída com sucesso!', 'success')
            
        except pymysql.Error as e:
            # Pode falhar por integridade referencial (se houver movimentações)
            flash(f'Erro ao excluir autopeça: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('autopecas'))

@app.route('/estoque')
def estoque():
    """
    ROTA DE GESTÃO DE ESTOQUE (/estoque)
    
    Funcionalidades:
    - Lista autopeças com situação de estoque
    - Exibe histórico de movimentações recentes
    - Permite registrar entradas/saídas
    - Destaca itens com estoque baixo
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Inicializa listas vazias para caso de erro
    autopecas_list = []
    movimentacoes = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # BUSCAR TODAS AS AUTOPEÇAS
            # Ordenadas alfabeticamente para facilitar localização
            cursor.execute("SELECT * FROM autopeca ORDER BY NOME_PECA")
            autopecas_list = cursor.fetchall()
            
            # BUSCAR HISTÓRICO DE MOVIMENTAÇÕES
            # JOIN com múltiplas tabelas para dados completos
            # LIMIT 10: apenas as 10 movimentações mais recentes
            cursor.execute("""
                SELECT m.*, a.NOME_PECA, u.NOME as usuario_nome
                FROM movimentacoes m
                JOIN autopeca a ON m.ID_PECA = a.ID_PECA
                JOIN usuario u ON m.ID_USUARIO = u.ID_USUARIO
                ORDER BY m.DATA_MOVI DESC
                LIMIT 10
            """)
            movimentacoes = cursor.fetchall()
            
        except pymysql.Error as e:
            flash(f'Erro ao carregar dados de estoque: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    # Passa ambas as listas para o template
    # Template pode iterar sobre elas e exibir dados
    return render_template('estoque.html', autopecas=autopecas_list, movimentacoes=movimentacoes)

@app.route('/movimentacao', methods=['POST'])
def add_movimentacao():
    """
    ROTA PARA REGISTRAR MOVIMENTAÇÃO DE ESTOQUE (/movimentacao)
    
    Método: POST (dados do formulário de movimentação)
    
    Tipos de movimentação:
    - ENTRADA: aumenta estoque (compras, devoluções)
    - SAÍDA: diminui estoque (vendas, perdas)
    
    Processo:
    1. Valida dados recebidos
    2. Verifica se há estoque suficiente (para saídas)
    3. Registra movimentação na tabela de histórico
    4. Atualiza estoque da autopeça
    5. Alerta se estoque ficou baixo
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_peca = int(request.form['id_peca'])
    quantidade = int(request.form['quantidade'])
    tipo_movimentacao = request.form['tipo_movimentacao']
    data = request.form.get('data')
    
    if not data:
        data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        try:
            # Buscar autopeça atual
            cursor.execute("SELECT * FROM autopeca WHERE ID_PECA = %s", (id_peca,))
            autopeca = cursor.fetchone()
            
            if not autopeca:
                flash('Autopeça não encontrada!', 'error')
                return redirect(url_for('estoque'))
            
            # Calcular novo estoque
            estoque_atual = autopeca['ESTOQUE']
            
            if tipo_movimentacao.upper() == 'ENTRADA':
                novo_estoque = estoque_atual + quantidade
            else:  # saída
                novo_estoque = estoque_atual - quantidade
                if novo_estoque < 0:
                    flash('Estoque insuficiente para esta movimentação!', 'error')
                    return redirect(url_for('estoque'))
            
            # Inserir movimentação
            cursor.execute("""
                INSERT INTO movimentacoes (ID_USUARIO, ID_PECA, DATA_MOVI, QUANTIDADE, TIPO_MOVI)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], id_peca, data, quantidade, tipo_movimentacao.upper()))
            
            # Atualizar estoque da autopeça
            cursor.execute("""
                UPDATE autopeca SET ESTOQUE = %s WHERE ID_PECA = %s
            """, (novo_estoque, id_peca))
            
            conn.commit()
            
            # Verificar estoque mínimo
            if novo_estoque < autopeca['ESTOQUE_MINIMO']:
                flash(f'ALERTA: Estoque da peça "{autopeca["NOME_PECA"]}" está abaixo do mínimo! Estoque atual: {novo_estoque}, Mínimo: {autopeca["ESTOQUE_MINIMO"]}', 'warning')
            else:
                flash('Movimentação registrada com sucesso!', 'success')
            
        except pymysql.Error as e:
            flash(f'Erro ao registrar movimentação: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('estoque'))

# ================================================================================
# EXECUÇÃO DA APLICAÇÃO
# ================================================================================

if __name__ == '__main__':
    """
    PONTO DE ENTRADA DA APLICAÇÃO
    
    Executa o servidor Flask quando o script é rodado diretamente.
    
    Parâmetros:
    - debug=True: Ativa modo de desenvolvimento
      * Recarrega automaticamente quando código muda
      * Mostra erros detalhados no navegador
      * NUNCA usar debug=True em produção!
    
    Para executar:
    python app.py
    
    Servidor iniciará em: http://127.0.0.1:5000
    """
    app.run(debug=True)


# ================================================================================
# GUIA COMPLETO PARA REPRODUZIR O PROJETO
# ================================================================================
"""
PASSO A PASSO PARA CONFIGURAR O SISTEMA:

1. INSTALAÇÃO DO AMBIENTE:
   - Instalar Python (3.7+): https://python.org
   - Instalar XAMPP: https://apachefriends.org
   - Instalar VS Code (opcional): https://code.visualstudio.com

2. CONFIGURAÇÃO DO BANCO DE DADOS:
   a) Iniciar XAMPP (Apache + MySQL)
   b) Acessar phpMyAdmin: http://localhost/phpmyadmin
   c) Criar banco 'saep_db'
   d) Executar SQL de criação das tabelas:

   CREATE TABLE usuarios (
       ID_USUARIO INT AUTO_INCREMENT PRIMARY KEY,
       EMAIL VARCHAR(100) NOT NULL UNIQUE,
       SENHA VARCHAR(255) NOT NULL,
       NOME_COMPLETO VARCHAR(150) NOT NULL
   );

   CREATE TABLE autopeca (
       ID_PECA INT AUTO_INCREMENT PRIMARY KEY,
       NOME_PECA VARCHAR(100) NOT NULL,
       NUM_SERIAL VARCHAR(50) NOT NULL,
       ESTOQUE INT NOT NULL DEFAULT 0,
       ESTOQUE_MINIMO INT NOT NULL DEFAULT 0,
       PRECO DECIMAL(10,2) NOT NULL,
       DESCRICAO TEXT,
       COMPATIBILIDADE VARCHAR(200)
   );

   -- Inserir usuário de teste
   INSERT INTO usuarios (EMAIL, SENHA, NOME_COMPLETO) 
   VALUES ('admin@saep.com', 'admin123', 'Administrador');

3. ESTRUTURA DE ARQUIVOS:
   projeto_saep/
   ├── app.py                    (este arquivo)
   ├── requirements.txt          (dependências)
   └── templates/
       ├── login.html
       ├── dashboard.html
       ├── autopecas.html        (comentado)
       ├── edit_autopeca.html
       └── estoque.html

4. INSTALAÇÃO DAS DEPENDÊNCIAS:
   pip install flask pymysql

   Ou criar requirements.txt:
   Flask==2.3.3
   PyMySQL==1.1.2

   E executar: pip install -r requirements.txt

5. CONFIGURAÇÃO DA CONEXÃO:
   - Verificar se MySQL está rodando (porta 3306)
   - Ajustar DB_CONFIG se necessário:
     * host: seu endereço do MySQL
     * user/password: suas credenciais
     * database: nome do seu banco

6. EXECUTAR A APLICAÇÃO:
   python app.py
   
   Acessar: http://localhost:5000
   Login: admin@saep.com / admin123

7. FUNCIONALIDADES DISPONÍVEIS:
   - Login de usuários
   - Dashboard com resumo
   - Cadastro de autopeças (CRUD completo)
   - Busca e filtros
   - Controle de estoque
   - Alertas de estoque baixo
   - Interface responsiva

8. SOLUÇÃO DE PROBLEMAS COMUNS:
   - "Connection refused": Verificar se MySQL está rodando
   - "Access denied": Verificar credenciais no DB_CONFIG
   - "Table doesn't exist": Criar tabelas no banco
   - "ModuleNotFoundError": Instalar dependências (pip install)

9. MELHORIAS PARA PRODUÇÃO:
   - Usar variáveis de ambiente para configurações
   - Implementar hash de senhas (werkzeug.security)
   - Adicionar validação de dados robusta
   - Configurar HTTPS
   - Usar gunicorn ou similar para servir
   - Implementar logs estruturados
   - Adicionar testes unitários

10. TECNOLOGIAS UTILIZADAS:
    - Backend: Flask (Python)
    - Banco: MySQL
    - Frontend: HTML5 + CSS3 + JavaScript
    - Templates: Jinja2
    - Conector DB: PyMySQL
    - Servidor: Flask development server

ESTE PROJETO É EDUCACIONAL E DEMONSTRA:
- Padrão MVC com Flask
- Operações CRUD completas
- Autenticação simples
- Interface responsiva
- Integração com banco de dados
- Tratamento de erros
- Sistema de mensagens flash
- Controle de sessão

Para dúvidas ou melhorias, consulte a documentação oficial:
- Flask: https://flask.palletsprojects.com
- PyMySQL: https://pymysql.readthedocs.io
- Jinja2: https://jinja.palletsprojects.com
"""