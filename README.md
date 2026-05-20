# ⚙️ AutoMecânica Pro — Flask + SQLite

Sistema web de gestão para oficina mecânica em **Python + Flask**, com banco de dados **SQLite** via **SQLAlchemy**.

---

## 📋 Pré-requisitos

- Python **3.10+**
- pip

---

## 🚀 Como rodar

### 1. Extraia e entre na pasta
```bash
cd oficina_flask
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute
```bash
python app.py
```

### 5. Acesse no navegador
```
http://127.0.0.1:5000
```

> O banco de dados (`instance/oficina.db`) é criado automaticamente na primeira execução, junto com dados iniciais de exemplo.

---

## 🔑 Credenciais de acesso

| Usuário         | E-mail                | Senha | Perfil       |
|-----------------|-----------------------|-------|--------------|
| Administrador   | admin@oficina.com     | 1234  | Admin        |
| João Mecânico   | joao@oficina.com      | 1234  | Operador     |

> O perfil **Admin** tem acesso ao módulo de gerenciamento de usuários.

---

## 🗄️ Banco de Dados

SQLite gerenciado pelo **Flask-SQLAlchemy**. Tabelas criadas automaticamente:

| Tabela           | Descrição                          |
|------------------|------------------------------------|
| `usuario`        | Usuários do sistema                |
| `cliente`        | Clientes da oficina                |
| `veiculo`        | Veículos (FK → cliente)            |
| `mecanico`       | Equipe de mecânicos                |
| `peca`           | Peças do estoque                   |
| `servico`        | Tabela de serviços / mão de obra   |
| `ordem_servico`  | Ordens de Serviço (FK → veiculo, mecanico) |
| `os_peca`        | Peças usadas em cada O.S.          |
| `os_servico`     | Serviços realizados em cada O.S.   |

Para resetar o banco (voltar aos dados iniciais):
```bash
# Apague o arquivo e reinicie o servidor
rm instance/oficina.db
python app.py
```

---

## 📁 Estrutura do projeto

```
oficina_flask/
├── app.py                  # Flask app — models, rotas, seed
├── requirements.txt
├── README.md
├── instance/
│   └── oficina.db          # SQLite (criado automaticamente)
└── templates/
    ├── base.html
    ├── auth/login.html
    ├── dashboard/painel.html
    ├── cliente/  (consultar, cadastrar, editar)
    ├── veiculo/  (consultar, cadastrar, editar)
    ├── os/       (consultar, cadastrar, editar, detalhes)
    ├── mecanico/ (consultar, cadastrar, editar)
    ├── peca/     (consultar, cadastrar, editar)
    ├── servico/  (consultar, cadastrar, editar)
    ├── usuario/  (consultar, cadastrar, editar)
    └── sobre/sobre.html
```

---

## 🛠️ Tecnologias

- **Python 3** + **Flask**
- **Flask-SQLAlchemy** + **SQLite**
- **Jinja2** (templates)
- **HTML5 / CSS3** puro — responsivo
