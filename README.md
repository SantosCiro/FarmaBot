# FarmaBot Pro v1.0 🧠💊

Chatbot SaaS para automação de atendimento em farmácias e pequenos negócios da área da saúde.

O FarmaBot responde perguntas frequentes, registra atendimentos e encaminha clientes para atendimento humano quando necessário.

---

## 🌐 Demo Online

https://farmabot-oh31.onrender.com/?c=poupalar

---

## 🎥 Demonstração

https://youtu.be/lClR_1Mau8Q

---

## 🚀 Funcionalidades

### 💬 Chat automatizado
- Responde perguntas frequentes com base em FAQ
- Identifica quando o usuário precisa de atendimento humano
- Fluxo simples e natural via chat

### 🎫 Sistema de tickets
- Coleta nome e telefone do cliente
- Cria ticket automaticamente
- Registra atendimento no banco de dados
- Painel para visualização de tickets

### ⚙️ Painel administrativo de FAQ
- Criar perguntas e respostas
- Editar base de conhecimento
- Atualizar comportamento do chatbot sem código

### 💾 Persistência de dados
- Dados armazenados em SQLite
- Informações mantidas mesmo após reiniciar o sistema

---

## 🏢 Arquitetura SaaS (Multiempresa)

O FarmaBot suporta múltiplas empresas através de um identificador na URL:

/poupalar/chat  
/poupalar/tickets  
/poupalar/faq  

Cada empresa possui:
- FAQ própria
- tickets próprios
- histórico isolado
- chatbot configurável

---

## 🛠 Tecnologias utilizadas

### Backend
- Python
- FastAPI

### Frontend
- HTML
- CSS
- JavaScript

### Banco de dados
- SQLite

---

## 🏗 Arquitetura do Projeto

```
farmabot/
├── backend/
│   ├── app.py
│   ├── db.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── tickets.html
│   └── faq.html
│
└── README.md
```

---

## ▶️ Executando localmente

### 1️⃣ Clonar o repositório
```
git clone https://github.com/SantosCiro/FarmaBot.git
```

### 2️⃣ Entrar na pasta
```
cd farmabot/backend
```

### 3️⃣ Criar ambiente virtual
```
python -m venv .venv
.venv\Scripts\activate
```

### 4️⃣ Instalar dependências
```
pip install -r requirements.txt
```

### 5️⃣ Rodar servidor
```
uvicorn app:app --reload
```

Acesse:
```
http://127.0.0.1:8000
```

---

## 🔮 Roadmap

### Versão 1.1
- Status de tickets
- Exportação CSV

### Versão 2.0
- Autenticação de administrador
- Integração com WhatsApp
- IA generativa (respostas inteligentes)
- Dashboard de métricas

---

## 🎯 Objetivo do projeto

Criar uma base sólida para um sistema SaaS de automação de atendimento, com foco em pequenos negócios.

---

## 👤 Autor

Ciro Leonardo dos Santos Barbosa

Foco em:
- Automação
- Inteligência Artificial
- Backend