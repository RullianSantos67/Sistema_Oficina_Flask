import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from functools import wraps

# static_folder='public' -> compatível com Vercel (serve estático via CDN a
# partir da pasta public/), e continua funcionando normalmente em localhost.
app = Flask(__name__, static_folder='public', static_url_path='')

# Em produção (Vercel), SECRET_KEY e DATABASE_URL vêm de variáveis de ambiente.
# Em desenvolvimento local, cai nos valores padrão abaixo (SQLite + chave fixa).
app.secret_key = os.environ.get('SECRET_KEY', 'automecanica-pro-dev-secret-trocar-em-producao')

_db_url = os.environ.get('DATABASE_URL', 'sqlite:///oficina.db')
if _db_url.startswith('postgres://'):          # Heroku/Neon às vezes retornam esse prefixo legado
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================
#  MODELS
# =============================================================

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    cpf        = db.Column(db.String(15),  unique=True, nullable=False)
    telefone   = db.Column(db.String(20))
    veiculos   = db.relationship('Veiculo', backref='cliente', lazy=True, cascade='all, delete-orphan')

class Mecanico(db.Model):
    __tablename__ = 'mecanico'
    id_mecanico   = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(50))
    ordens        = db.relationship('OrdemServico', backref='mecanico', lazy=True)

class Peca(db.Model):
    __tablename__ = 'peca'
    id_peca            = db.Column(db.Integer, primary_key=True)
    descricao          = db.Column(db.String(150), nullable=False)
    preco_base         = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade_estoque = db.Column(db.Integer, default=0)

class Servico(db.Model):
    __tablename__ = 'servico'
    id_servico = db.Column(db.Integer, primary_key=True)
    descricao  = db.Column(db.String(150), nullable=False)
    valor_hora = db.Column(db.Numeric(10, 2), nullable=False)

class Veiculo(db.Model):
    __tablename__ = 'veiculo'
    id_veiculo = db.Column(db.Integer, primary_key=True)
    placa      = db.Column(db.String(10),  unique=True, nullable=False)
    marca      = db.Column(db.String(50))
    modelo     = db.Column(db.String(50))
    ano        = db.Column(db.Integer)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente', ondelete='CASCADE'), nullable=False)
    ordens     = db.relationship('OrdemServico', backref='veiculo', lazy=True, cascade='all, delete-orphan')

class OrdemServico(db.Model):
    __tablename__ = 'ordem_servico'
    id_os         = db.Column(db.Integer, primary_key=True)
    data_entrada  = db.Column(db.Date, nullable=False)
    data_previsao = db.Column(db.Date)
    status        = db.Column(db.String(30), default='Aberta')
    valor_total   = db.Column(db.Numeric(10, 2), default=0.00)
    id_veiculo    = db.Column(db.Integer, db.ForeignKey('veiculo.id_veiculo',   ondelete='CASCADE'),  nullable=False)
    id_mecanico   = db.Column(db.Integer, db.ForeignKey('mecanico.id_mecanico', ondelete='RESTRICT'), nullable=False)
    pecas_os      = db.relationship('OsPeca',    backref='ordem', lazy=True, cascade='all, delete-orphan')
    servicos_os   = db.relationship('OsServico', backref='ordem', lazy=True, cascade='all, delete-orphan')

class OsPeca(db.Model):
    __tablename__ = 'os_peca'
    id_os          = db.Column(db.Integer, db.ForeignKey('ordem_servico.id_os', ondelete='CASCADE'),  primary_key=True)
    id_peca        = db.Column(db.Integer, db.ForeignKey('peca.id_peca',        ondelete='RESTRICT'), primary_key=True)
    quantidade     = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    peca           = db.relationship('Peca')

class OsServico(db.Model):
    __tablename__ = 'os_servico'
    id_os         = db.Column(db.Integer, db.ForeignKey('ordem_servico.id_os',   ondelete='CASCADE'),  primary_key=True)
    id_servico    = db.Column(db.Integer, db.ForeignKey('servico.id_servico',    ondelete='RESTRICT'), primary_key=True)
    horas_gastas  = db.Column(db.Numeric(5, 2), nullable=False)
    valor_cobrado = db.Column(db.Numeric(10, 2), nullable=False)
    servico       = db.relationship('Servico')

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    senha      = db.Column(db.String(255), nullable=False)
    perfil     = db.Column(db.String(20), default='operador')


# =============================================================
#  SEED
# =============================================================

def seed_database():
    if Usuario.query.first():
        return

    db.session.add_all([
        Usuario(nome='Administrador', email='admin@oficina.com', senha=generate_password_hash('1234'), perfil='admin'),
        Usuario(nome='Joao Mecanico',  email='joao@oficina.com',  senha=generate_password_hash('1234'), perfil='operador'),
    ])

    c1 = Cliente(nome='Carlos Pereira',  cpf='123.456.789-00', telefone='(35) 99999-1111')
    c2 = Cliente(nome='Ana Souza',       cpf='987.654.321-00', telefone='(35) 98888-2222')
    c3 = Cliente(nome='Ricardo Almeida', cpf='456.123.789-00', telefone='(35) 97777-3333')
    db.session.add_all([c1, c2, c3])

    m1 = Mecanico(nome='Lucas Ferreira', especialidade='Motor e Cambio')
    m2 = Mecanico(nome='Pedro Oliveira', especialidade='Suspensao e Freios')
    m3 = Mecanico(nome='Marcos Ribeiro', especialidade='Eletrica Automotiva')
    db.session.add_all([m1, m2, m3])

    p1 = Peca(descricao='Filtro de Oleo',       preco_base=35.90,  quantidade_estoque=12)
    p2 = Peca(descricao='Pastilha de Freio',    preco_base=89.90,  quantidade_estoque=3)
    p3 = Peca(descricao='Correia Dentada',      preco_base=120.00, quantidade_estoque=5)
    p4 = Peca(descricao='Vela de Ignicao',      preco_base=22.50,  quantidade_estoque=2)
    p5 = Peca(descricao='Fluido de Freio DOT4', preco_base=18.00,  quantidade_estoque=8)
    db.session.add_all([p1, p2, p3, p4, p5])

    s1 = Servico(descricao='Troca de Oleo e Filtro',      valor_hora=80.00)
    s2 = Servico(descricao='Alinhamento e Balanceamento', valor_hora=120.00)
    s3 = Servico(descricao='Revisao Eletrica',            valor_hora=150.00)
    s4 = Servico(descricao='Troca de Pastilha de Freio',  valor_hora=100.00)
    db.session.add_all([s1, s2, s3, s4])

    db.session.flush()

    v1 = Veiculo(placa='ABC-1234', marca='Fiat',       modelo='Uno',  ano=2019, id_cliente=c1.id_cliente)
    v2 = Veiculo(placa='XYZ-5678', marca='Volkswagen', modelo='Gol',  ano=2021, id_cliente=c2.id_cliente)
    v3 = Veiculo(placa='DEF-9012', marca='Chevrolet',  modelo='Onix', ano=2022, id_cliente=c3.id_cliente)
    db.session.add_all([v1, v2, v3])
    db.session.flush()

    os1 = OrdemServico(data_entrada=date(2026,5,10), data_previsao=date(2026,5,18),
                       status='Em Andamento', valor_total=380.90,
                       id_veiculo=v1.id_veiculo, id_mecanico=m1.id_mecanico)
    os2 = OrdemServico(data_entrada=date(2026,5,12), data_previsao=date(2026,5,20),
                       status='Aguardando Pecas', valor_total=120.00,
                       id_veiculo=v2.id_veiculo, id_mecanico=m2.id_mecanico)
    os3 = OrdemServico(data_entrada=date(2026,5,1), data_previsao=date(2026,5,5),
                       status='Concluida', valor_total=540.00,
                       id_veiculo=v3.id_veiculo, id_mecanico=m3.id_mecanico)
    db.session.add_all([os1, os2, os3])
    db.session.flush()

    db.session.add_all([
        OsPeca(id_os=os1.id_os, id_peca=p1.id_peca, quantidade=1, preco_unitario=35.90),
        OsPeca(id_os=os1.id_os, id_peca=p2.id_peca, quantidade=2, preco_unitario=89.90),
        OsPeca(id_os=os3.id_os, id_peca=p3.id_peca, quantidade=1, preco_unitario=120.00),
        OsServico(id_os=os1.id_os, id_servico=s1.id_servico, horas_gastas=1.0, valor_cobrado=80.00),
        OsServico(id_os=os1.id_os, id_servico=s4.id_servico, horas_gastas=0.5, valor_cobrado=85.20),
        OsServico(id_os=os2.id_os, id_servico=s2.id_servico, horas_gastas=1.0, valor_cobrado=120.00),
        OsServico(id_os=os3.id_os, id_servico=s3.id_servico, horas_gastas=2.0, valor_cobrado=300.00),
        OsServico(id_os=os3.id_os, id_servico=s1.id_servico, horas_gastas=1.0, valor_cobrado=80.00),
    ])
    db.session.commit()


# =============================================================
#  HELPERS
# =============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        if session.get('usuario_nivel') != 'admin':
            flash('Acesso restrito ao administrador.', 'erro')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def format_brl(value):
    try:
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return 'R$ 0,00'

app.jinja_env.globals['format_brl'] = format_brl


# =============================================================
#  AUTH
# =============================================================

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id']    = usuario.id_usuario
            session['usuario_nome']  = usuario.nome
            session['usuario_nivel'] = usuario.perfil
            return redirect(url_for('dashboard'))
        else:
            erro = 'E-mail ou senha incorretos.'
    return render_template('auth/login.html', erro=erro, controller='auth')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# =============================================================
#  DASHBOARD
# =============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    total_cli    = Cliente.query.count()
    total_vei    = Veiculo.query.count()
    total_os     = OrdemServico.query.filter(OrdemServico.status != 'Concluida').count()
    pecas_baixas = Peca.query.filter(Peca.quantidade_estoque <= 3).count()
    return render_template('dashboard/painel.html', controller='dashboard',
                           totalCli=total_cli, totalVei=total_vei,
                           totalOs=total_os, pecasBaixas=pecas_baixas)


# =============================================================
#  SOBRE
# =============================================================

@app.route('/sobre')
@login_required
def sobre():
    return render_template('sobre/sobre.html', controller='institucional')


# =============================================================
#  CLIENTES
# =============================================================

@app.route('/cliente')
@login_required
def cliente_consultar():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('cliente/consultar.html', controller='cliente', clientes=clientes)

@app.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def cliente_cadastrar():
    if request.method == 'POST':
        try:
            db.session.add(Cliente(
                nome=request.form['nome'].strip(),
                cpf=request.form['cpf'].strip(),
                telefone=request.form['telefone'].strip()))
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'sucesso')
            return redirect(url_for('cliente_consultar'))
        except Exception:
            db.session.rollback()
            flash('Erro: CPF ja cadastrado ou dados invalidos.', 'erro')
    return render_template('cliente/cadastrar.html', controller='cliente')

@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    cli = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        try:
            cli.nome=request.form['nome'].strip(); cli.cpf=request.form['cpf'].strip(); cli.telefone=request.form['telefone'].strip()
            db.session.commit()
            flash('Cliente atualizado!', 'sucesso')
            return redirect(url_for('cliente_consultar'))
        except Exception:
            db.session.rollback(); flash('Erro: CPF ja em uso.', 'erro')
    return render_template('cliente/editar.html', controller='cliente', cliente=cli)

@app.route('/cliente/excluir/<int:id>')
@login_required
def cliente_excluir(id):
    cli = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cli); db.session.commit(); flash('Cliente removido.', 'sucesso')
    except Exception:
        db.session.rollback(); flash('Nao e possivel excluir: cliente tem veiculos vinculados.', 'erro')
    return redirect(url_for('cliente_consultar'))


# =============================================================
#  VEICULOS
# =============================================================

@app.route('/veiculo')
@login_required
def veiculo_consultar():
    rows = (db.session.query(Veiculo, Cliente.nome.label('dono'))
            .join(Cliente, Veiculo.id_cliente == Cliente.id_cliente)
            .order_by(Veiculo.placa).all())
    return render_template('veiculo/consultar.html', controller='veiculo', veiculos=rows)

@app.route('/veiculo/novo', methods=['GET', 'POST'])
@login_required
def veiculo_cadastrar():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    if request.method == 'POST':
        try:
            db.session.add(Veiculo(
                placa=request.form['placa'].strip().upper(),
                marca=request.form['marca'].strip(),
                modelo=request.form['modelo'].strip(),
                ano=int(request.form['ano']),
                id_cliente=int(request.form['id_cliente'])))
            db.session.commit()
            flash('Veiculo registrado!', 'sucesso')
            return redirect(url_for('veiculo_consultar'))
        except Exception:
            db.session.rollback(); flash('Erro: placa ja cadastrada.', 'erro')
    return render_template('veiculo/cadastrar.html', controller='veiculo', clientes=clientes)

@app.route('/veiculo/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def veiculo_editar(id):
    vei = Veiculo.query.get_or_404(id)
    clientes = Cliente.query.order_by(Cliente.nome).all()
    if request.method == 'POST':
        try:
            vei.placa=request.form['placa'].strip().upper(); vei.marca=request.form['marca'].strip()
            vei.modelo=request.form['modelo'].strip(); vei.ano=int(request.form['ano'])
            vei.id_cliente=int(request.form['id_cliente'])
            db.session.commit(); flash('Veiculo atualizado!', 'sucesso')
            return redirect(url_for('veiculo_consultar'))
        except Exception:
            db.session.rollback(); flash('Erro: placa ja em uso.', 'erro')
    return render_template('veiculo/editar.html', controller='veiculo', veiculo=vei, clientes=clientes)

@app.route('/veiculo/excluir/<int:id>')
@login_required
def veiculo_excluir(id):
    vei = Veiculo.query.get_or_404(id)
    try:
        db.session.delete(vei); db.session.commit(); flash('Veiculo removido.', 'sucesso')
    except Exception:
        db.session.rollback(); flash('Nao e possivel excluir: veiculo tem O.S. vinculadas.', 'erro')
    return redirect(url_for('veiculo_consultar'))


# =============================================================
#  MECANICOS
# =============================================================

@app.route('/mecanico')
@login_required
def mecanico_consultar():
    return render_template('mecanico/consultar.html', controller='mecanico',
                           mecanicos=Mecanico.query.order_by(Mecanico.nome).all())

@app.route('/mecanico/novo', methods=['GET', 'POST'])
@login_required
def mecanico_cadastrar():
    if request.method == 'POST':
        db.session.add(Mecanico(nome=request.form['nome'].strip(), especialidade=request.form['especialidade'].strip()))
        db.session.commit(); flash('Mecanico cadastrado!', 'sucesso')
        return redirect(url_for('mecanico_consultar'))
    return render_template('mecanico/cadastrar.html', controller='mecanico')

@app.route('/mecanico/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def mecanico_editar(id):
    mec = Mecanico.query.get_or_404(id)
    if request.method == 'POST':
        mec.nome=request.form['nome'].strip(); mec.especialidade=request.form['especialidade'].strip()
        db.session.commit(); flash('Mecanico atualizado!', 'sucesso')
        return redirect(url_for('mecanico_consultar'))
    return render_template('mecanico/editar.html', controller='mecanico', mecanico=mec)

@app.route('/mecanico/excluir/<int:id>')
@login_required
def mecanico_excluir(id):
    mec = Mecanico.query.get_or_404(id)
    try:
        db.session.delete(mec); db.session.commit(); flash('Mecanico removido.', 'sucesso')
    except Exception:
        db.session.rollback(); flash('Nao e possivel excluir: mecanico tem O.S. vinculadas.', 'erro')
    return redirect(url_for('mecanico_consultar'))


# =============================================================
#  PECAS
# =============================================================

@app.route('/peca')
@login_required
def peca_consultar():
    return render_template('peca/consultar.html', controller='peca',
                           pecas=Peca.query.order_by(Peca.descricao).all())

@app.route('/peca/nova', methods=['GET', 'POST'])
@login_required
def peca_cadastrar():
    if request.method == 'POST':
        db.session.add(Peca(descricao=request.form['descricao'].strip(),
                            preco_base=float(request.form['preco_base']),
                            quantidade_estoque=int(request.form['quantidade_estoque'])))
        db.session.commit(); flash('Peca adicionada!', 'sucesso')
        return redirect(url_for('peca_consultar'))
    return render_template('peca/cadastrar.html', controller='peca')

@app.route('/peca/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def peca_editar(id):
    peca = Peca.query.get_or_404(id)
    if request.method == 'POST':
        peca.descricao=request.form['descricao'].strip()
        peca.preco_base=float(request.form['preco_base'])
        peca.quantidade_estoque=int(request.form['quantidade_estoque'])
        db.session.commit(); flash('Peca atualizada!', 'sucesso')
        return redirect(url_for('peca_consultar'))
    return render_template('peca/editar.html', controller='peca', peca=peca)

@app.route('/peca/excluir/<int:id>')
@login_required
def peca_excluir(id):
    peca = Peca.query.get_or_404(id)
    try:
        db.session.delete(peca); db.session.commit(); flash('Peca removida.', 'sucesso')
    except Exception:
        db.session.rollback(); flash('Nao e possivel excluir: peca usada em alguma O.S.', 'erro')
    return redirect(url_for('peca_consultar'))


# =============================================================
#  SERVICOS
# =============================================================

@app.route('/servico')
@login_required
def servico_consultar():
    return render_template('servico/consultar.html', controller='servico',
                           servicos=Servico.query.order_by(Servico.descricao).all())

@app.route('/servico/novo', methods=['GET', 'POST'])
@login_required
def servico_cadastrar():
    if request.method == 'POST':
        db.session.add(Servico(descricao=request.form['descricao'].strip(),
                               valor_hora=float(request.form['valor_hora'])))
        db.session.commit(); flash('Servico adicionado!', 'sucesso')
        return redirect(url_for('servico_consultar'))
    return render_template('servico/cadastrar.html', controller='servico')

@app.route('/servico/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def servico_editar(id):
    srv = Servico.query.get_or_404(id)
    if request.method == 'POST':
        srv.descricao=request.form['descricao'].strip(); srv.valor_hora=float(request.form['valor_hora'])
        db.session.commit(); flash('Servico atualizado!', 'sucesso')
        return redirect(url_for('servico_consultar'))
    return render_template('servico/editar.html', controller='servico', servico=srv)

@app.route('/servico/excluir/<int:id>')
@login_required
def servico_excluir(id):
    srv = Servico.query.get_or_404(id)
    try:
        db.session.delete(srv); db.session.commit(); flash('Servico removido.', 'sucesso')
    except Exception:
        db.session.rollback(); flash('Nao e possivel excluir: servico usado em alguma O.S.', 'erro')
    return redirect(url_for('servico_consultar'))


# =============================================================
#  ORDENS DE SERVICO
# =============================================================

@app.route('/os')
@login_required
def os_consultar():
    ordens = (db.session.query(OrdemServico, Veiculo.placa, Cliente.nome.label('cliente'))
              .join(Veiculo, OrdemServico.id_veiculo == Veiculo.id_veiculo)
              .join(Cliente, Veiculo.id_cliente == Cliente.id_cliente)
              .order_by(OrdemServico.id_os.desc()).all())
    return render_template('os/consultar.html', controller='os', ordens=ordens)

@app.route('/os/nova', methods=['GET', 'POST'])
@login_required
def os_cadastrar():
    veiculos  = (db.session.query(Veiculo, Cliente.nome.label('dono')).join(Cliente).order_by(Veiculo.placa).all())
    mecanicos = Mecanico.query.order_by(Mecanico.nome).all()
    if request.method == 'POST':
        db.session.add(OrdemServico(
            data_entrada=date.today(),
            data_previsao=date.fromisoformat(request.form['data_previsao']),
            status=request.form['status'], valor_total=0.00,
            id_veiculo=int(request.form['id_veiculo']),
            id_mecanico=int(request.form['id_mecanico'])))
        db.session.commit(); flash('O.S. aberta com sucesso!', 'sucesso')
        return redirect(url_for('os_consultar'))
    return render_template('os/cadastrar.html', controller='os', veiculos=veiculos, mecanicos=mecanicos)

@app.route('/os/detalhes/<int:id>')
@login_required
def os_detalhes(id):
    os_ = OrdemServico.query.get_or_404(id)
    pecas_disponiveis = Peca.query.filter(Peca.quantidade_estoque > 0).order_by(Peca.descricao).all()
    servicos_disponiveis = Servico.query.order_by(Servico.descricao).all()
    return render_template('os/detalhes.html', controller='os', os=os_,
                           pecas_usadas=os_.pecas_os, servicos_feitos=os_.servicos_os,
                           pecas_disponiveis=pecas_disponiveis, servicos_disponiveis=servicos_disponiveis)


def _recalcular_total_os(ordem):
    """Soma peças + mão de obra lançadas na O.S. e atualiza o valor_total."""
    total_pecas    = sum(float(op.preco_unitario) * op.quantidade for op in ordem.pecas_os)
    total_servicos = sum(float(os_s.valor_cobrado) for os_s in ordem.servicos_os)
    ordem.valor_total = round(total_pecas + total_servicos, 2)


@app.route('/os/<int:id>/peca/adicionar', methods=['POST'])
@login_required
def os_adicionar_peca(id):
    ordem = OrdemServico.query.get_or_404(id)
    if ordem.status == 'Concluida':
        flash('O.S. concluída não pode ser alterada.', 'erro')
        return redirect(url_for('os_detalhes', id=id))
    try:
        id_peca    = int(request.form['id_peca'])
        quantidade = int(request.form['quantidade'])
    except (ValueError, KeyError):
        flash('Dados inválidos.', 'erro')
        return redirect(url_for('os_detalhes', id=id))

    peca = Peca.query.get_or_404(id_peca)
    if quantidade <= 0:
        flash('Informe uma quantidade válida.', 'erro')
        return redirect(url_for('os_detalhes', id=id))
    if quantidade > peca.quantidade_estoque:
        flash(f'Estoque insuficiente para "{peca.descricao}". Disponível: {peca.quantidade_estoque} un.', 'erro')
        return redirect(url_for('os_detalhes', id=id))

    item_existente = OsPeca.query.filter_by(id_os=id, id_peca=id_peca).first()
    if item_existente:
        item_existente.quantidade += quantidade
    else:
        db.session.add(OsPeca(id_os=id, id_peca=id_peca, quantidade=quantidade, preco_unitario=peca.preco_base))

    peca.quantidade_estoque -= quantidade
    db.session.flush()
    _recalcular_total_os(ordem)
    db.session.commit()
    flash(f'{quantidade}x "{peca.descricao}" lançada(s) na O.S.! Estoque atualizado.', 'sucesso')
    return redirect(url_for('os_detalhes', id=id))


@app.route('/os/<int:id>/peca/remover/<int:id_peca>')
@login_required
def os_remover_peca(id, id_peca):
    ordem = OrdemServico.query.get_or_404(id)
    if ordem.status == 'Concluida':
        flash('O.S. concluída não pode ser alterada.', 'erro')
        return redirect(url_for('os_detalhes', id=id))
    item = OsPeca.query.filter_by(id_os=id, id_peca=id_peca).first_or_404()
    peca = Peca.query.get(id_peca)
    if peca:
        peca.quantidade_estoque += item.quantidade   # estorna o estoque
    db.session.delete(item)
    db.session.flush()
    _recalcular_total_os(ordem)
    db.session.commit()
    flash('Peça removida da O.S. e estoque estornado.', 'sucesso')
    return redirect(url_for('os_detalhes', id=id))


@app.route('/os/<int:id>/servico/adicionar', methods=['POST'])
@login_required
def os_adicionar_servico(id):
    ordem = OrdemServico.query.get_or_404(id)
    if ordem.status == 'Concluida':
        flash('O.S. concluída não pode ser alterada.', 'erro')
        return redirect(url_for('os_detalhes', id=id))
    try:
        id_servico = int(request.form['id_servico'])
        horas      = float(request.form['horas_gastas'])
    except (ValueError, KeyError):
        flash('Dados inválidos.', 'erro')
        return redirect(url_for('os_detalhes', id=id))

    if horas <= 0:
        flash('Informe um tempo válido.', 'erro')
        return redirect(url_for('os_detalhes', id=id))

    servico = Servico.query.get_or_404(id_servico)
    valor = round(horas * float(servico.valor_hora), 2)

    item_existente = OsServico.query.filter_by(id_os=id, id_servico=id_servico).first()
    if item_existente:
        item_existente.horas_gastas  = float(item_existente.horas_gastas) + horas
        item_existente.valor_cobrado = round(float(item_existente.valor_cobrado) + valor, 2)
    else:
        db.session.add(OsServico(id_os=id, id_servico=id_servico, horas_gastas=horas, valor_cobrado=valor))

    db.session.flush()
    _recalcular_total_os(ordem)
    db.session.commit()
    flash(f'Serviço "{servico.descricao}" lançado na O.S.!', 'sucesso')
    return redirect(url_for('os_detalhes', id=id))


@app.route('/os/<int:id>/servico/remover/<int:id_servico>')
@login_required
def os_remover_servico(id, id_servico):
    ordem = OrdemServico.query.get_or_404(id)
    if ordem.status == 'Concluida':
        flash('O.S. concluída não pode ser alterada.', 'erro')
        return redirect(url_for('os_detalhes', id=id))
    item = OsServico.query.filter_by(id_os=id, id_servico=id_servico).first_or_404()
    db.session.delete(item)
    db.session.flush()
    _recalcular_total_os(ordem)
    db.session.commit()
    flash('Serviço removido da O.S.', 'sucesso')
    return redirect(url_for('os_detalhes', id=id))

@app.route('/os/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def os_editar(id):
    os_ = OrdemServico.query.get_or_404(id)
    veiculos  = (db.session.query(Veiculo, Cliente.nome.label('dono')).join(Cliente).order_by(Veiculo.placa).all())
    mecanicos = Mecanico.query.order_by(Mecanico.nome).all()
    if request.method == 'POST':
        os_.id_veiculo=int(request.form['id_veiculo']); os_.id_mecanico=int(request.form['id_mecanico'])
        os_.status=request.form['status']; os_.data_previsao=date.fromisoformat(request.form['data_previsao'])
        db.session.commit(); flash('O.S. atualizada!', 'sucesso')
        return redirect(url_for('os_consultar'))
    return render_template('os/editar.html', controller='os', os=os_, veiculos=veiculos, mecanicos=mecanicos)

@app.route('/os/concluir/<int:id>')
@login_required
def os_concluir(id):
    os_ = OrdemServico.query.get_or_404(id)
    os_.status = 'Concluida'; db.session.commit()
    flash('O.S. encerrada!', 'sucesso')
    return redirect(url_for('os_consultar'))

@app.route('/os/excluir/<int:id>')
@login_required
def os_excluir(id):
    os_ = OrdemServico.query.get_or_404(id)
    db.session.delete(os_); db.session.commit()
    flash('O.S. removida.', 'sucesso')
    return redirect(url_for('os_consultar'))


# =============================================================
#  RELATORIOS
# =============================================================

@app.route('/relatorios')
@login_required
def relatorios():
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim    = request.args.get('data_fim', '').strip()

    query = OrdemServico.query.filter(OrdemServico.status == 'Concluida')
    if data_inicio:
        query = query.filter(OrdemServico.data_entrada >= date.fromisoformat(data_inicio))
    if data_fim:
        query = query.filter(OrdemServico.data_entrada <= date.fromisoformat(data_fim))
    ordens_concluidas = query.all()

    faturamento_total  = sum(float(o.valor_total) for o in ordens_concluidas)
    qtd_os_concluidas  = len(ordens_concluidas)
    ticket_medio       = (faturamento_total / qtd_os_concluidas) if qtd_os_concluidas else 0

    por_mecanico = (db.session.query(Mecanico.nome,
                                     db.func.count(OrdemServico.id_os),
                                     db.func.coalesce(db.func.sum(OrdemServico.valor_total), 0))
                    .join(OrdemServico, OrdemServico.id_mecanico == Mecanico.id_mecanico)
                    .filter(OrdemServico.status == 'Concluida')
                    .group_by(Mecanico.id_mecanico)
                    .order_by(Mecanico.nome).all())

    pecas_mais_usadas = (db.session.query(Peca.descricao, db.func.sum(OsPeca.quantidade).label('total'))
                         .join(OsPeca, OsPeca.id_peca == Peca.id_peca)
                         .group_by(Peca.id_peca)
                         .order_by(db.desc('total')).limit(5).all())

    status_contagem = (db.session.query(OrdemServico.status, db.func.count(OrdemServico.id_os))
                       .group_by(OrdemServico.status).all())

    pecas_estoque_baixo = Peca.query.filter(Peca.quantidade_estoque <= 3).order_by(Peca.quantidade_estoque).all()

    return render_template('relatorio/relatorio.html', controller='relatorio',
                           faturamento_total=faturamento_total, qtd_os_concluidas=qtd_os_concluidas,
                           ticket_medio=ticket_medio, por_mecanico=por_mecanico,
                           pecas_mais_usadas=pecas_mais_usadas, status_contagem=status_contagem,
                           pecas_estoque_baixo=pecas_estoque_baixo,
                           data_inicio=data_inicio, data_fim=data_fim)


# =============================================================
#  USUARIOS (ADMIN)
# =============================================================

@app.route('/usuario')
@admin_required
def usuario_consultar():
    return render_template('usuario/consultar.html', controller='usuario',
                           usuarios=Usuario.query.order_by(Usuario.nome).all())

@app.route('/usuario/novo', methods=['GET', 'POST'])
@admin_required
def usuario_cadastrar():
    if request.method == 'POST':
        try:
            db.session.add(Usuario(nome=request.form['nome'].strip(),
                                   email=request.form['email'].strip(),
                                   senha=generate_password_hash(request.form['senha']),
                                   perfil=request.form['perfil']))
            db.session.commit(); flash('Usuario criado!', 'sucesso')
            return redirect(url_for('usuario_consultar'))
        except Exception:
            db.session.rollback(); flash('Erro: e-mail ja cadastrado.', 'erro')
    return render_template('usuario/cadastrar.html', controller='usuario')

@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def usuario_editar(id):
    usr = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        try:
            usr.nome=request.form['nome'].strip(); usr.email=request.form['email'].strip()
            usr.perfil=request.form['perfil']
            if request.form.get('senha'): usr.senha=generate_password_hash(request.form['senha'])
            db.session.commit(); flash('Usuario atualizado!', 'sucesso')
            return redirect(url_for('usuario_consultar'))
        except Exception:
            db.session.rollback(); flash('Erro: e-mail ja em uso.', 'erro')
    return render_template('usuario/editar.html', controller='usuario', usuario=usr)

@app.route('/usuario/excluir/<int:id>')
@admin_required
def usuario_excluir(id):
    if id == session.get('usuario_id'):
        flash('Voce nao pode excluir sua propria conta.', 'erro')
        return redirect(url_for('usuario_consultar'))
    usr = Usuario.query.get_or_404(id)
    db.session.delete(usr); db.session.commit()
    flash('Usuario removido.', 'sucesso')
    return redirect(url_for('usuario_consultar'))


# =============================================================
#  INICIALIZACAO
# =============================================================

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    app.run(debug=True)
