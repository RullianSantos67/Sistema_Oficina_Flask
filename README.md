# ⚙️ AutoMecânica Pro — Flask + SQLite/PostgreSQL

Sistema web completo de gestão para oficina mecânica em **Python + Flask**, com banco de dados via **SQLAlchemy** (SQLite em desenvolvimento, PostgreSQL em produção).

---

## ✅ Funcionalidades

- **CRUD completo** de Clientes, Veículos, Mecânicos, Peças, Serviços, Ordens de Serviço e Usuários.
- **Login com senha protegida por hash** (Werkzeug `pbkdf2:sha256`) — nenhuma senha é armazenada em texto puro.
- **Controle de permissões em 2 níveis**:
  - **Admin**: acesso total, incluindo o módulo de gerenciamento de usuários.
  - **Operador**: acesso a todos os módulos operacionais (clientes, veículos, O.S., estoque, relatórios), sem acesso ao cadastro de usuários do sistema.
- **Fluxo completo de Ordem de Serviço**: lançamento de peças e mão de obra direto na tela de detalhes da O.S., com:
  - baixa automática no estoque ao lançar uma peça (e estorno automático se a peça for removida da O.S.);
  - validação de estoque insuficiente;
  - recálculo automático do `valor_total` da O.S. a cada lançamento/remoção;
  - bloqueio de qualquer alteração depois que a O.S. é marcada como **Concluída**.
- **Relatórios gerenciais** (`/relatorios`): faturamento por período, faturamento por mecânico, ticket médio, peças mais usadas, O.S. por status e alerta de estoque crítico.
- **Frontend responsivo**: tabelas em desktop, cards em mobile, menu lateral retrátil.
- **Proteção contra SQL Injection**: 100% das consultas via ORM (SQLAlchemy), sem SQL concatenado manualmente.

---

## 📋 Pré-requisitos

- Python **3.10+**
- pip

---

## 🚀 Como rodar localmente

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
> `psycopg2-binary` só é realmente usado em produção (PostgreSQL). Em desenvolvimento local o app cai automaticamente em SQLite, então a instalação funciona normalmente mesmo sem um Postgres configurado.

### 4. Execute
```bash
python app.py
```

### 5. Acesse no navegador
```
http://127.0.0.1:5000
```

> O banco de dados (`instance/oficina.db`) é criado automaticamente na primeira execução, junto com dados iniciais de exemplo (seed).

---

## 🔑 Credenciais de acesso

| Usuário         | E-mail                | Senha | Perfil       |
|-----------------|------------------------|-------|--------------|
| Administrador   | admin@oficina.com     | 1234  | Admin        |
| João Mecânico   | joao@oficina.com      | 1234  | Operador     |

> As senhas acima já são armazenadas com hash no banco — `1234` é apenas a senha em texto plano usada para *fazer login*, nunca o que fica gravado.

---

## 🗄️ Banco de Dados

Gerenciado pelo **Flask-SQLAlchemy**. Tabelas criadas automaticamente:

| Tabela           | Descrição                                  |
|------------------|---------------------------------------------|
| `usuario`        | Usuários do sistema (senha em hash)         |
| `cliente`        | Clientes da oficina                         |
| `veiculo`        | Veículos (FK → cliente)                     |
| `mecanico`       | Equipe de mecânicos                         |
| `peca`           | Peças do estoque                            |
| `servico`        | Tabela de serviços / valor da hora          |
| `ordem_servico`  | Ordens de Serviço (FK → veiculo, mecanico)  |
| `os_peca`        | Peças lançadas em cada O.S. (baixa estoque) |
| `os_servico`     | Serviços/mão de obra lançados em cada O.S.  |

Para resetar o banco local (voltar aos dados iniciais):
```bash
rm instance/oficina.db
python app.py
```

---

## ☁️ Deploy na Vercel

A Vercel detecta automaticamente a instância Flask (`app`) dentro de `app.py` na raiz do projeto — **não é necessário `vercel.json`**.

### 1. Banco de dados (obrigatório)
O sistema de arquivos da Vercel é **somente leitura/efêmero** em produção: o SQLite local **não persiste** entre requisições. Antes de publicar:

1. No dashboard da Vercel, vá em **Storage → Create Database** e crie um Postgres (via Neon, parceiro oficial da Vercel).
2. Isso injeta automaticamente a variável de ambiente `DATABASE_URL` no projeto — o `app.py` já está preparado para usá-la (cai em SQLite só se a variável não existir).

### 2. Variáveis de ambiente
Em **Settings → Environment Variables**, defina:
- `SECRET_KEY` → uma string aleatória qualquer (ex.: gere com `python -c "import secrets; print(secrets.token_hex(32))"`).
- `DATABASE_URL` → já preenchida automaticamente se você criou o banco pelo passo acima.

### 3. Publicar
```bash
git init
git add .
git commit -m "AutoMecânica Pro"
git push origin main
```
Importe o repositório direto no dashboard da Vercel (**Add New → Project**). Cada push na branch principal gera um novo deploy automaticamente.

> Os arquivos estáticos (`public/css/`) já são servidos via CDN da Vercel — nenhum ajuste extra é necessário, o projeto já está com a estrutura de pastas correta para isso.

---

## 📁 Estrutura do projeto

```
oficina_flask/
├── app.py                  # Flask app — models, rotas, regras de negócio, seed
├── requirements.txt
├── README.md
├── .gitignore
├── public/css/              # Estático (servido via CDN na Vercel)
├── instance/
│   └── oficina.db           # SQLite local (criado automaticamente, ignorado no git)
└── templates/
    ├── base.html
    ├── auth/login.html
    ├── dashboard/painel.html
    ├── cliente/   (consultar, cadastrar, editar)
    ├── veiculo/   (consultar, cadastrar, editar)
    ├── os/        (consultar, cadastrar, editar, detalhes)
    ├── mecanico/  (consultar, cadastrar, editar)
    ├── peca/      (consultar, cadastrar, editar)
    ├── servico/   (consultar, cadastrar, editar)
    ├── usuario/   (consultar, cadastrar, editar)
    ├── relatorio/relatorio.html
    └── sobre/sobre.html
```

---

## 🛠️ Tecnologias

- **Python 3** + **Flask**
- **Flask-SQLAlchemy** + **SQLite** (dev) / **PostgreSQL** (produção)
- **Werkzeug Security** — hash de senha
- **Jinja2** (templates)
- **HTML5 / CSS3** puro — responsivo
