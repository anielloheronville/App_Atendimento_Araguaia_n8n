Implantação do App de Ficha de Atendimento no Render

Este guia explica como implantar a aplicação Flask (Python) com um banco de dados PostgreSQL no Render.com.

Arquivos Necessários

Você precisará destes três arquivos:

app.py (O aplicativo principal)

requirements.txt (Define as dependências do Python)

README.md (Este arquivo)

Passos para Implantação

Siga estes passos no painel do Render:

Criar o Banco de Dados (PostgreSQL)
Primeiro, crie o banco de dados para que ele esteja pronto para o aplicativo.

Vá em New + > PostgreSQL.

Dê um nome (ex: araguaia-db).

Escolha a Região (ex: US East ou Frankfurt).

Escolha o plano Free.

Clique em Create Database.

Aguarde alguns minutos até o status ser "Available".

Após a criação, vá até a página do banco de dados e copie a Internal Connection URL. Guarde-a, você precisará dela.

Criar o Aplicativo Web (Web Service)
Agora, implante o aplicativo app.py.

Vá em New + > Web Service.

Conecte seu repositório (GitHub, GitLab) onde o app.py e requirements.txt estão.

Dê um nome ao seu serviço (ex: araguaia-app).

Configure o serviço:

Environment: Python

Build Command: pip install -r requirements.txt && python -c 'import app; app.init_db()'

O que isso faz: Instala as bibliotecas e depois executa a função init_db() do seu app.py para criar a tabela.

Start Command: gunicorn app:app

O que isso faz: Inicia o servidor web de produção (gunicorn) para rodar o seu app (Flask).

Escolha o plano Free.

Adicionar a Variável de Ambiente
O aplicativo (Web Service) precisa saber onde o banco de dados está.

Antes de clicar em "Create Web Service" (ou nas Configurações/Environment do serviço, se já o criou), vá para a seção Environment Variables.

Clique em Add Environment Variable.

Key: DATABASE_URL

Value: Cole a Internal Connection URL que você copiou do seu banco de dados no Passo 1.

(Opcional) Adicione uma variável de fuso horário:

Key: TZ

Value: America/Cuiaba (ou o fuso de Sorriso/MT)

Finalizar
Clique em Create Web Service.

O Render irá construir e implantar seu aplicativo. Você pode assistir ao log em "Logs".

A primeira implantação (build) pode demorar alguns minutos.

Quando o status for "Live" ou "Available", você poderá acessar a URL pública (ex: https://araguaia-app.onrender.com) e seu aplicativo estará funcionando, conectado ao banco de dados PostgreSQL.

Teste Local (Opcional)

Se quiser testar localmente, você precisa ter o Python e um banco de dados PostgreSQL rodando na sua máquina (ex: via Postgres.app para Mac ou instalando-o no Windows/Linux).

Instale as bibliotecas: pip install -r requirements.txt

Defina a variável de ambiente para apontar para o seu banco local.

Mac/Linux: export DATABASE_URL='postgresql://usuario:senha@localhost:5432/nomedobanco'

Windows (CMD): set DATABASE_URL='postgresql://usuario:senha@localhost:5432/nomedobanco'

Execute o aplicativo: python app.py
