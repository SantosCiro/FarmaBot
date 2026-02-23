FarmaBot 🧠💊

🎥 **Demonstração em vídeo:**  
https://youtu.be/ogz0HUaN8Cc


“📌 Demo local: abra frontend/index.html e frontend/tickets.html”

Chatbot de atendimento inicial para farmácias com escalonamento humano e painel de tickets

O FarmaBot é um chatbot web desenvolvido para automatizar o atendimento inicial de farmácias e pequenos negócios da área da saúde.
Ele responde perguntas frequentes, identifica quando não consegue ajudar e encaminha automaticamente o atendimento para um humano, registrando tudo em um painel de tickets.

⚠️ O bot não realiza diagnósticos nem indica medicamentos. Ele atua apenas no atendimento operacional inicial.

🚀 Funcionalidades

💬 Chat de atendimento online (simulador de WhatsApp no navegador)

📋 Respostas automáticas para perguntas frequentes:

Horário de funcionamento

Entrega e retirada

Disponibilidade de medicamentos

Endereço e contato

Receita médica e genéricos

🧠 Escalonamento inteligente

Quando o bot não entende ou o usuário pede um humano

Solicita nome e telefone antes de abrir o ticket

🎫 Abertura automática de tickets

📊 Painel de tickets no navegador

💾 Armazenamento local com SQLite

💰 Zero custo para rodar localmente

🛠️ Tecnologias Utilizadas

Backend: Python + FastAPI

Frontend: HTML, CSS e JavaScript puro

Banco de dados: SQLite

Servidor: Uvicorn

📂 Estrutura do Projeto
farmabot/
├── backend/
│   ├── app.py          # API e lógica do chatbot
│   ├── db.py           # Banco de dados e tickets
│   ├── faq.json        # Base de conhecimento (FAQ)
│   ├── requirements.txt
│   └── tickets.db      # Criado automaticamente
│
└── frontend/
    ├── index.html      # Chat do usuário
    └── tickets.html   # Painel de tickets

▶️ Como Rodar o Projeto Localmente
1️⃣ Clonar o repositório
git clone <url-do-repositorio>
cd farmabot/backend

2️⃣ Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate   # Windows

3️⃣ Instalar dependências
pip install -r requirements.txt

4️⃣ Iniciar o servidor
uvicorn app:app --reload


A API ficará disponível em:

http://127.0.0.1:8000

🌐 Abrindo as Interfaces

Chat do usuário:
Abra frontend/index.html no navegador

Painel de tickets:
Abra frontend/tickets.html no navegador

🧪 Fluxo de Teste Sugerido

Abra o chat

Digite:

quero falar com atendente


O bot pedirá nome e telefone

Informe algo como:

João 21999998888


Abra o painel de tickets e clique em Atualizar

O ticket aparecerá no topo da lista ✅

🎯 Objetivo do Projeto

Este projeto foi desenvolvido como:

📌 Portfólio prático

📌 MVP de produto real

📌 Base para futuras integrações (WhatsApp, IA generativa, multiusuário)

🔮 Próximos Passos (Evoluções Possíveis)

Integração com WhatsApp Business API

Uso de IA para entendimento semântico das mensagens

Autenticação de atendentes

Multiempresas (várias farmácias)

Dashboard com métricas de atendimento

👤 Autor

Desenvolvido por Ciro Leonardo dos Santos Barbosa
📍 Brasil
💡 Foco em Dados, Automação e Inteligência Artificial aplicada a negócios
