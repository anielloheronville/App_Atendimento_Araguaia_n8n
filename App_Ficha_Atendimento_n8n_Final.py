import flask
from flask import Flask, request, render_template_string, jsonify
import psycopg2
import os
import datetime
import requests
import logging

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração da Aplicação ---
app = Flask(__name__)

def to_bool_flag(value):
    """Converte valores vindos do front/n8n para booleano."""
    if value is None:
        return False
    value_str = str(value).strip().lower()
    return value_str in ('1', 'true', 'sim', 'yes')

# --- CONFIGURAÇÕES DE PRODUÇÃO (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTA DE EMPREENDIMENTOS (Dropdown) ---
OPCOES_EMPREENDIMENTOS = [
    "Jardim dos Ipês", "Jardim Amazônia ET. 3", "Jardim Amazônia ET. 4", 
    "Jardim Amazônia ET. 5", "Jardim Paulista", "Jardim Mato Grosso", 
    "Jardim Florencia", "Benjamim Rossato", "Santa Felicidade", "Amazon Park", 
    "Santa Fé", "Colina Verde", "Res. Terra de Santa Cruz", "Consórcio Gran Ville", 
    "Consórcio Parque Cerrado", "Consórcio Recanto da Mata", "Jardim Vila Rica", 
    "Jardim Amazônia Et. I", "Jardim Amazônia Et. II", "Loteamento Luxemburgo", 
    "Loteamento Jardim Vila Bella", "Morada do Boque III", "Reserva Jardim", 
    "Residencial Cidade Jardim", "Residencial Florais da Mata", 
    "Residencial Jardim Imigrantes", "Residencial Vila Rica", 
    "Residencial Vila Rica SINOP", "Outro / Não Listado"
]

# --- LISTA DE CORRETORES ---
OPCOES_CORRETORES = [
    "4083 - NEURA.T.PAVAN SINIGAGLIA", "2796 - PEDRO LAERTE RABECINI", 
    "57 - Santos e Padilha Ltda - ME", "1376 - VALMIR MARIO TOMASI", 
    "1768 - SEGALA EMPREENDIMENTOS", "2436 - PAULO EDUARDO GONCALVES DIAS", 
    "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO", "4476 - Priscila Canhet da Silveira", 
    "1531 - Walmir de Oliveira Queiroz", "4704 - MAYCON JEAN CAMPOS", 
    "4084 - JAIMIR COMPAGNONI", "4096 - THAYANE APARECIDA BORGES", 
    "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA", "4587 - GABRIEL GALVÃO LOURENÇO", 
    "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR", "4868 - LENE ENGLER DA SILVA", 
    "4087 - JOHNNY MIRANDA OJEDA", "4531 - MG EMPREENDIMENTOS LTDA", 
    "4826 - JEVIELI BELLO OLIVEIRA", "4825 - EVA VITORIA GALVAO LOURENCO", 
    "54 - Ronaldo Padilha dos Santos", "1137 - Moacir Blemer Olivoto", 
    "4872 - WQ CORRETORES LTDA", "720 - Luciane Bocchi ME", 
    "5154 - FELIPE JOSE MOREIRA ALMEIDA", "3063 - SILVANA SEGALA", 
    "2377 - Paulo Eduardo Gonçalves Dias", "Outro / Não Listado"
]

# --- BANCO DE DADOS ---
def init_db():
    if not DATABASE_URL:
        logger.warning("⚠️ AVISO: DATABASE_URL não encontrada. O app não salvará dados.")
        return

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS atendimentos (
        id SERIAL PRIMARY KEY,
        data_hora TIMESTAMPTZ NOT NULL,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        rede_social TEXT,
        abordagem_inicial TEXT,
        esteve_plantao BOOLEAN,
        foi_atendido BOOLEAN,
        nome_corretor TEXT,
        autoriza_transmissao BOOLEAN,
        foto_cliente TEXT,
        assinatura TEXT,
        cidade TEXT,
        loteamento TEXT
    )
    '''
    # Migrações
    migrations = [
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nota_atendimento INTEGER DEFAULT 0;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empreendimento_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS quadra_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS lote_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS m2_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_m2_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_total_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS venda_realizada_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS forma_pagamento_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS entrada_forma_pagamento_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS numero_parcelas_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_parcelas_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vencimento_parcelas_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nome_proponente_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS rg_proponente_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS orgao_emissor_proponente_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cpf_proponente_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS estado_civil_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS filhos_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS endereco_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_residencial_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS celular_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS email_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_residencia_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_aluguel_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_financiamento_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_financiamento_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empresa_trabalha_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS profissao_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_empresa_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS renda_mensal_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nome_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS rg_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS orgao_emissor_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cpf_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS email_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empresa_trabalha_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS profissao_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_empresa_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS renda_mensal_conjuge_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS referencias_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS fonte_midia_pc TEXT;"
    ]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        for migration in migrations:
            try:
                cursor.execute(migration)
            except Exception:
                pass 
        cursor.close()
        conn.close()
        logger.info("✅ Banco de dados atualizado.")
    except Exception as e:
        logger.error(f"❌ Erro crítico DB: {e}")

init_db()

# --- TEMPLATE HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Araguaia Imóveis - Ficha Digital</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Font Montserrat -->
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
    <!-- HTML2PDF -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <!-- SweetAlert2 (Alertas Bonitos) -->
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <!-- jQuery e InputMask (Máscaras de Input) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.8/jquery.inputmask.min.js"></script>
    
    <style>
        :root {
            --cor-bg-fundo: #263318; 
            --cor-bg-form: #324221;
            --cor-acento: #8cc63f; 
            --cor-texto-claro: #ffffff;
            --cor-texto-cinza: #d1d5db;
            --cor-borda: #4a5e35;
        }

        body {
            background-color: var(--cor-bg-fundo);
            color: var(--cor-texto-claro);
            font-family: 'Montserrat', sans-serif;
        }

        .form-container {
            background-color: var(--cor-bg-form);
            border-radius: 0.75rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--cor-borda);
            transition: all 0.3s ease;
        }

        /* --- Títulos de Seção Estilizados (Tarja Verde com Ícone) --- */
        .section-header {
            width: 100%;
            background-color: var(--cor-acento);
            color: #1a2610; /* Texto escuro */
            font-weight: 800;
            text-transform: uppercase;
            padding: 0.6rem 1rem;
            border-radius: 0.375rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.5rem; /* Espaço entre ícone e texto */
        }
        
        /* SVG Icon styling */
        .section-icon {
            width: 1.2em;
            height: 1.2em;
            fill: currentColor;
        }

        .logo-text { font-weight: 800; letter-spacing: -0.05em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .logo-line { height: 4px; background-color: var(--cor-acento); width: 100px; margin: 0.5rem auto; border-radius: 2px; }

        .form-input, .form-textarea, .form-select {
            background-color: #263318;
            border: 1px solid var(--cor-borda);
            color: var(--cor-texto-claro);
            border-radius: 0.5rem;
            padding: 0.75rem;
            width: 100%;
            transition: all 0.3s;
        }
        
        .form-input:focus, .form-textarea:focus, .form-select:focus {
            border-color: var(--cor-acento);
            outline: none;
            box-shadow: 0 0 0 2px rgba(140, 198, 63, 0.2);
        }

        .btn-salvar {
            background-color: var(--cor-acento);
            color: #1a2610;
            font-weight: 800;
            padding: 0.85rem 2rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            cursor: pointer;
            text-transform: uppercase;
        }
        .btn-salvar:hover { background-color: #7ab82e; transform: translateY(-1px); }
        .btn-salvar:disabled { opacity: 0.6; cursor: not-allowed; }

        .btn-pdf {
            background-color: #ffffff;
            color: #263318;
            font-weight: 700;
            padding: 0.85rem 1.5rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            cursor: pointer;
            text-transform: uppercase;
            margin-right: 10px;
        }

        .signature-canvas, .photo-canvas, .video-preview {
            border: 2px dashed var(--cor-borda);
            border-radius: 0.5rem;
            background-color: rgba(0,0,0,0.2);
        }

        .btn-acao-secundaria {
            color: var(--cor-texto-cinza);
            font-size: 0.85rem;
            text-decoration: underline;
            cursor: pointer;
        }
        
        .hidden { display: none; }
        
        /* PDF MODE */
        .pdf-mode {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 20px !important;
        }
        .pdf-mode .form-input, .pdf-mode .form-textarea, .pdf-mode .form-select {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        .pdf-mode .section-header {
            background-color: #eee !important;
            color: #000 !important;
            border: 1px solid #000;
            box-shadow: none;
        }
        .pdf-mode label, .pdf-mode span, .pdf-mode p { color: #000 !important; }
        .pdf-mode .section-icon { fill: #000; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <header class="w-full p-6 text-center">
        <h1 class="text-4xl md:text-5xl logo-text text-white">Araguaia</h1>
        <h2 class="text-xl md:text-2xl font-semibold text-white mt-1">Imóveis</h2>
        <div class="logo-line"></div>
    </header>

    <main class="flex-grow flex items-center justify-center p-4">
        <div id="fichaContainer" class="form-container w-full max-w-4xl mx-auto p-6 md:p-10">
            <div id="pdfHeader" class="hidden text-center mb-4">
                <h1 class="text-3xl font-bold text-[#263318]">FICHA DE ATENDIMENTO / PRÉ-CONTRATO</h1>
                <hr class="border-[#8cc63f] my-2">
            </div>

            <form id="preAtendimentoForm" class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                <!-- DADOS INICIAIS -->
                <div class="flex flex-col gap-5">
                    <div><label class="block text-sm font-semibold mb-2 text-white">Nome do Cliente*</label><input type="text" id="nome" name="nome" class="form-input" required></div>
                    
                    <!-- INPUTMASK TELEFONE -->
                    <div><label class="block text-sm font-semibold mb-2 text-white">Telefone / WhatsApp*</label>
                        <input type="tel" id="telefone" name="telefone" class="form-input mask-phone" placeholder="(XX) XXXXX-XXXX" inputmode="tel" required>
                    </div>
                    
                    <div><label class="block text-sm font-semibold mb-2 text-gray-300">Instagram / Facebook</label><input type="text" id="rede_social" name="rede_social" class="form-input"></div>
                    <div><label class="block text-sm font-semibold mb-2 text-white">Cidade do Atendimento*</label><input type="text" id="cidade" name="cidade" class="form-input" required></div>
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-white">Loteamento / Empreendimento</label>
                        <select id="loteamento" name="loteamento" class="form-select">
                            <option value="" disabled selected>Selecione...</option>
                            {% for opcao in empreendimentos %}<option value="{{ opcao }}">{{ opcao }}</option>{% endfor %}
                        </select>
                    </div>
                    <!-- Gatilho -->
                    <div>
                        <label for="comprou_1o_lote" class="block text-sm font-semibold mb-2 text-white">Realizou o sonho da compra do 1º Lote?</label>
                        <select id="comprou_1o_lote" name="comprou_1o_lote" class="form-select" required>
                            <option value="" disabled selected>Selecione...</option>
                            <option value="Sim">Sim</option>
                            <option value="Não">Não</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-white">Nível de Interesse</label>
                        <select id="nivel_interesse" name="nivel_interesse" class="form-select">
                            <option value="Alto">Alto</option><option value="Médio">Médio</option><option value="Baixo">Baixo</option>
                        </select>
                    </div>
                </div>

                <!-- LADO DIREITO (Foto e Perguntas) -->
                <div class="flex flex-col gap-5">
                    <div class="p-4 rounded-lg bg-black/20 border border-white/10" id="photoContainer">
                        <label class="block text-sm font-semibold mb-3 text-white">Foto do Cliente</label>
                        <div class="flex flex-col items-center gap-3">
                            <div class="relative">
                                <canvas id="photoCanvas" class="photo-canvas w-32 h-32 rounded-full object-cover"></canvas>
                                <video id="videoPreview" class="video-preview w-32 h-32 rounded-full object-cover hidden" autoplay playsinline></video>
                            </div>
                            <div class="flex flex-wrap justify-center gap-2" data-html2canvas-ignore="true">
                                <button type="button" id="startWebcam" class="text-xs bg-gray-700 text-white px-3 py-2 rounded">📷 Câmera</button>
                                <button type="button" id="takePhoto" class="hidden text-xs bg-green-600 text-white px-3 py-2 rounded">📸 Capturar</button>
                                <button type="button" id="clearPhoto" class="hidden text-xs text-red-400 underline">Remover</button>
                            </div>
                        </div>
                        <input type="hidden" id="foto_cliente_base64" name="foto_cliente_base64">
                    </div>

                    <div class="space-y-4">
                        <div><span class="block text-sm font-semibold mb-2 text-white">Já esteve em um plantão?*</span>
                            <div class="flex gap-4"><label class="flex items-center"><input type="radio" name="esteve_plantao" value="sim" required class="accent-[#8cc63f]"><span class="ml-2 text-white">Sim</span></label><label class="flex items-center"><input type="radio" name="esteve_plantao" value="nao" class="accent-[#8cc63f]"><span class="ml-2 text-white">Não</span></label></div>
                        </div>
                        <div><span class="block text-sm font-semibold mb-2 text-white">Já possui corretor?*</span>
                            <div class="flex gap-4"><label class="flex items-center"><input type="radio" name="foi_atendido" value="sim" id="atendido_sim" required class="accent-[#8cc63f]"><span class="ml-2 text-white">Sim</span></label><label class="flex items-center"><input type="radio" name="foi_atendido" value="nao" id="atendido_nao" class="accent-[#8cc63f]"><span class="ml-2 text-white">Não</span></label></div>
                        </div>
                        <div id="campoNomeCorretor" class="hidden p-3 bg-[#8cc63f]/10 border border-[#8cc63f] rounded-md">
                            <label class="block text-sm font-bold mb-1 text-[#8cc63f]">Selecione o Corretor:</label>
                            <select id="nome_corretor" name="nome_corretor" class="form-select font-semibold">
                                <option value="" disabled selected>Selecione...</option>
                                {% for corretor in corretores %}<option value="{{ corretor }}">{{ corretor }}</option>{% endfor %}
                            </select>
                        </div>
                        <div><span class="block text-sm font-semibold mb-2 text-white">Autoriza lista de transmissão?*</span>
                            <div class="flex gap-4"><label class="flex items-center"><input type="radio" name="autoriza_transmissao" value="sim" required class="accent-[#8cc63f]"><span class="ml-2 text-white">Sim</span></label><label class="flex items-center"><input type="radio" name="autoriza_transmissao" value="nao" class="accent-[#8cc63f]"><span class="ml-2 text-white">Não</span></label></div>
                        </div>
                    </div>
                </div>
                
                <div class="md:col-span-2">
                    <label class="block text-sm font-semibold mb-2 text-white">Observações / Abordagem Inicial</label>
                    <textarea id="abordagem_inicial" name="abordagem_inicial" rows="3" class="form-textarea"></textarea>
                </div>

                <!-- ============================
                     FICHA DE CADASTRO / PRÉ-CONTRATO
                     ============================ -->
                <div id="preContratoSection" class="md:col-span-2 hidden border border-[var(--cor-acento)] rounded-lg p-6 bg-black/20 mt-4 transition-all duration-500">
                    <h2 class="text-2xl font-bold mb-4 text-[#8cc63f] text-center uppercase tracking-wide">Ficha de Cadastro - Pré-Contrato</h2>

                    <!-- 1ª PARTE - DADOS DO IMÓVEL -->
                    <div class="section-header">
                        <!-- Ícone Casinha -->
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                        Dados do Imóvel
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">Empreendimento</label><input type="text" name="empreendimento_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">QD</label><input type="text" name="quadra_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">LT</label><input type="text" name="lote_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">M²</label><input type="text" name="m2_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <!-- MASK MONEY -->
                        <div><label class="block text-xs font-semibold mb-1 text-white">VL. M²</label><input type="text" name="vl_m2_pc" class="form-input mask-money" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">VL. Total</label><input type="text" name="vl_total_pc" class="form-input mask-money" inputmode="numeric"></div>
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Corretor (Opcional)</label><input type="text" id="corretor_pc" class="form-input"></div>
                    </div>

                    <!-- 2ª PARTE - FORMA DE PAGAMENTO -->
                    <div class="section-header">
                         <!-- Ícone Cifrão -->
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M12.5 17.5h-4v-1.9c-1.3-.4-2.1-1.4-2.1-2.6 0-1.8 1.5-2.8 3.5-3.1v-2c-.9.1-1.6.5-1.9.9l-1.3-1c.6-.9 1.7-1.5 3.2-1.7V4h1.9v2c1.4.3 2.3 1.4 2.3 2.6 0 1.8-1.5 2.8-3.5 3.1v2.2c1.1-.1 1.9-.6 2.3-1.1l1.3 1c-.6 1.1-1.9 1.9-3.7 2.1v1.6zM10.4 9.1c0 .5.4.9 1.6 1.1v-2c-.9.1-1.6.4-1.6.9zm3.2 5.9c0-.6-.5-1-1.6-1.1v2.1c.9-.1 1.6-.4 1.6-1z"/></svg>
                        Forma de Pagamento
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-4">
                            <span class="block text-xs font-semibold mb-1 text-white">Venda realizada:</span>
                            <div class="flex flex-wrap gap-4">
                                <label class="flex items-center text-xs text-white"><input type="radio" name="venda_realizada_pc" value="Estabelecimento Comercial" class="accent-[#8cc63f] mr-1"> Estab. Comercial</label>
                                <label class="flex items-center text-xs text-white"><input type="radio" name="venda_realizada_pc" value="Telefone" class="accent-[#8cc63f] mr-1"> Telefone</label>
                                <label class="flex items-center text-xs text-white"><input type="radio" name="venda_realizada_pc" value="Domicílio" class="accent-[#8cc63f] mr-1"> Domicílio</label>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2">
                            <label class="block text-xs font-semibold mb-1 text-white">Entrada / Forma de Pagamento</label>
                            <input type="text" name="entrada_forma_pagamento_pc" class="form-input" placeholder="R$ / condição">
                        </div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Nº Parcelas</label><input type="number" name="numero_parcelas_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">VL. Parcelas</label><input type="text" name="vl_parcelas_pc" class="form-input mask-money" inputmode="numeric"></div>
                    </div>
                    <div class="mb-4">
                        <span class="block text-xs font-semibold mb-1 text-white">Vencimento das parcelas:</span>
                        <div class="flex gap-4">
                            <label class="flex items-center text-xs text-white"><input type="radio" name="vencimento_parcelas_pc" value="10" class="accent-[#8cc63f] mr-1"> Dia 10</label>
                            <label class="flex items-center text-xs text-white"><input type="radio" name="vencimento_parcelas_pc" value="20" class="accent-[#8cc63f] mr-1"> Dia 20</label>
                            <label class="flex items-center text-xs text-white"><input type="radio" name="vencimento_parcelas_pc" value="30" class="accent-[#8cc63f] mr-1"> Dia 30</label>
                        </div>
                    </div>

                    <!-- 3ª PARTE - DADOS DO PROPONENTE -->
                    <div class="section-header">
                        <!-- Ícone Usuário -->
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                        Dados do Proponente
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Nome</label><input type="text" name="nome_proponente_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">RG</label><input type="text" name="rg_proponente_pc" class="form-input" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Órgão Emissor</label><input type="text" name="orgao_emissor_proponente_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <!-- MASK CPF -->
                        <div><label class="block text-xs font-semibold mb-1 text-white">CPF</label><input type="tel" name="cpf_proponente_pc" class="form-input mask-cpf" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Estado Civil</label><input type="text" name="estado_civil_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Filhos</label><input type="text" name="filhos_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Endereço</label><input type="text" name="endereco_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Residencial</label><input type="tel" name="tel_residencial_pc" class="form-input mask-phone" inputmode="tel"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">Celular</label><input type="tel" name="celular_pc" class="form-input mask-phone" inputmode="tel"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">E-mail</label><input type="email" name="email_pc" class="form-input"></div>
                        <div>
                            <span class="block text-xs font-semibold mb-1 text-white">Residência:</span>
                            <div class="flex gap-3">
                                <label class="flex items-center text-xs text-white"><input type="radio" name="possui_residencia_pc" value="Propria" class="accent-[#8cc63f] mr-1"> Própria</label>
                                <label class="flex items-center text-xs text-white"><input type="radio" name="possui_residencia_pc" value="Alugada" class="accent-[#8cc63f] mr-1"> Alugada</label>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3 items-end">
                        <div><label class="block text-xs font-semibold mb-1 text-white">Valor Aluguel</label><input type="text" name="valor_aluguel_pc" class="form-input mask-money" inputmode="numeric"></div>
                        <div class="md:col-span-2">
                            <span class="block text-xs font-semibold mb-1 text-white">Possui Financiamento:</span>
                            <div class="flex flex-wrap gap-3">
                                <label class="flex items-center text-xs text-white"><input type="radio" name="possui_financiamento_pc" value="Nao" class="accent-[#8cc63f] mr-1"> Não</label>
                                <label class="flex items-center text-xs text-white"><input type="radio" name="possui_financiamento_pc" value="Veiculos" class="accent-[#8cc63f] mr-1"> Veículos</label>
                                <label class="flex items-center text-xs text-white"><input type="radio" name="possui_financiamento_pc" value="Imoveis" class="accent-[#8cc63f] mr-1"> Imóveis</label>
                            </div>
                        </div>
                        <div>
                             <!-- NOVO CAMPO VALOR -->
                            <label class="block text-xs font-semibold mb-1 text-white">Valor (R$)</label>
                            <input type="text" name="valor_financiamento_pc" class="form-input mask-money" inputmode="numeric">
                        </div>
                    </div>

                    <!-- 4ª PARTE - DADOS PROFISSIONAIS -->
                    <div class="section-header">
                        <!-- Ícone Maleta -->
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>
                        Dados Profissionais
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Empresa</label><input type="text" name="empresa_trabalha_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Profissão</label><input type="text" name="profissao_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Empresa</label><input type="tel" name="tel_empresa_pc" class="form-input mask-phone" inputmode="tel"></div>
                    </div>
                    <div><label class="block text-xs font-semibold mb-1 text-white">Renda Mensal</label><input type="text" name="renda_mensal_pc" class="form-input w-full md:w-1/3 mask-money" inputmode="numeric"></div>

                    <!-- 5ª PARTE - DADOS DO CÔNJUGE -->
                    <div class="section-header">
                        <!-- Ícone Coração/Pessoas -->
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                        Dados do Cônjuge
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Nome</label><input type="text" name="nome_conjuge_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">RG</label><input type="text" name="rg_conjuge_pc" class="form-input" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Órgão Emissor</label><input type="text" name="orgao_emissor_conjuge_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">CPF</label><input type="tel" name="cpf_conjuge_pc" class="form-input mask-cpf" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Contato</label><input type="tel" name="tel_conjuge_pc" class="form-input mask-phone" inputmode="tel"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">E-mail</label><input type="email" name="email_conjuge_pc" class="form-input"></div>
                    </div>

                    <!-- 6ª PARTE - PROFISSIONAL CÔNJUGE -->
                    <div class="section-header">Dados Profissionais do Cônjuge</div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Empresa</label><input type="text" name="empresa_trabalha_conjuge_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Profissão</label><input type="text" name="profissao_conjuge_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Empresa</label><input type="tel" name="tel_empresa_conjuge_pc" class="form-input mask-phone" inputmode="tel"></div>
                    </div>
                    <div><label class="block text-xs font-semibold mb-1 text-white">Renda Mensal</label><input type="text" name="renda_mensal_conjuge_pc" class="form-input w-full md:w-1/3 mask-money" inputmode="numeric"></div>

                    <!-- 7ª PARTE - REFERÊNCIAS -->
                    <div class="section-header">
                        <!-- Ícone Grupo -->
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M12 12.75c1.63 0 3.07.39 4.24.9 1.08.48 1.76 1.56 1.76 2.73V18H6v-1.61c0-1.18.68-2.26 1.76-2.73 1.17-.52 2.61-.91 4.24-.91zM4 13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm1.13 1.1c-.37-.06-.74-.1-1.13-.1-2.21 0-4 1.79-4 4v2h4v-2c0-.81.25-1.56.64-2.19l.49.29zM19.13 14.1l.49-.29c.39.63.64 1.38.64 2.19v2h4v-2c0-2.21-1.79-4-4-4-.39 0-.76.04-1.13.1zM12 12c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3z"/></svg>
                        Referências Comerciais e Pessoais
                    </div>
                    <div class="space-y-2 mb-4">
                        {% for i in range(1,6) %}
                        <div class="grid grid-cols-5 gap-2">
                            <div class="col-span-3"><label class="block text-xs font-semibold mb-1 text-white">Nome {{ i }}</label><input type="text" name="ref_nome_{{ i }}" class="form-input"></div>
                            <div class="col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Tel. {{ i }}</label><input type="tel" name="ref_tel_{{ i }}" class="form-input mask-phone" inputmode="tel"></div>
                        </div>
                        {% endfor %}
                    </div>

                    <!-- 8ª PARTE - FONTE -->
                    <div class="section-header">
                        <!-- Ícone Megafone -->
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M2 17h2v.5H3v1h1v.5H2v1h3v-4H2v1zm1 9h2v-.5H3v-1h1v-.5H2v-1h3v4H2v-1zm-1-9h2v-.5H2v-1h1v-.5H2v-1h3v4H2v-1zM7 9h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zm0 4h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zM7 4h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zM12 2l-5 5H2v6h5l5 5V2zm0 0"/></svg>
                        Fonte de Mídia
                    </div>
                    <div class="flex flex-wrap gap-3 mb-4">
                        {% for label, value in [('Placa','Placa'),('Jornal','Jornal'),('Site','Site'),('Outdoor','Outdoor'),('TV','TV'),('Panfleto','Panfleto'),('Indicação','Indicacao'),('Outros','Outros')] %}
                        <label class="flex items-center text-xs text-white"><input type="checkbox" name="fonte_midia_pc" value="{{ value }}" class="accent-[#8cc63f] mr-1"> {{ label }}</label>
                        {% endfor %}
                    </div>

                    <!-- 9ª PARTE - CONDIÇÕES -->
                    <div class="section-header">
                        <!-- Ícone Documento -->
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg>
                        Condições Gerais
                    </div>
                    <div class="text-[0.7rem] leading-tight text-gray-200 mb-6 text-justify">
                        <p class="mb-2">1. O promitente comprador formaliza a intenção de adquirir o imóvel descrito acima de maneira irrevogável e irretratável...</p>
                        <p class="mb-2">2. A ausência da assinatura do Contrato de Compromisso de Venda e Compra do Imóvel pelo COMPRADOR no prazo estipulado...</p>
                        <p>3. Fica estipulado que o Foro da Comarca de Sorriso - MT será o competente para a resolução de quaisquer questões...</p>
                    </div>

                    <!-- ASSINATURAS COM ESPAÇAMENTO AUMENTADO -->
                    <div class="mt-8 text-xs text-white">
                        <p class="mb-12 font-bold text-lg">De Acordo,</p> <!-- mb-12 para dar espaço -->
                        
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-12 mb-12"> <!-- gap-12 para espaçamento horizontal, mb-12 para linhas -->
                            <div class="text-center pt-8 border-t border-gray-400">COMPRADOR</div>
                            <div class="text-center pt-8 border-t border-gray-400">CORRETOR</div>
                            <div class="text-center pt-8 border-t border-gray-400">PROPRIETÁRIO/APROVAÇÃO</div>
                            <div class="text-center pt-8 border-t border-gray-400">LOCAL / DATA</div>
                        </div>
                        <div class="grid grid-cols-2 gap-12">
                            <div class="text-center pt-8 border-t border-gray-400">TESTEMUNHA 1</div>
                            <div class="text-center pt-8 border-t border-gray-400">TESTEMUNHA 2</div>
                        </div>
                    </div>
                </div>

                <!-- ASSINATURA DIGITAL -->
                <div class="md:col-span-2 mt-4">
                    <label class="block text-sm font-semibold mb-2 text-white">Assinatura Digital (Canvas)</label>
                    <canvas id="signatureCanvas" class="signature-canvas w-full h-32 cursor-crosshair"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="flex justify-end mt-1"><button type="button" id="clearSignature" class="btn-acao-secundaria">Limpar Assinatura</button></div>
                </div>

                <div class="md:col-span-2 flex flex-col md:flex-row justify-end items-center gap-4 mt-4 btn-area">
                    <button type="button" id="btnGerarPDF" class="btn-pdf w-full md:w-auto shadow-lg">📄 Baixar Cópia (PDF)</button>
                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto shadow-lg hover:shadow-xl">Salvar Ficha</button>
                </div>
            </form>
        </div>
    </main>
    <footer class="w-full p-6 text-center text-xs opacity-50">© 2024 Araguaia Imóveis.</footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            
            // --- INICIALIZAÇÃO DAS MÁSCARAS (jQuery InputMask) ---
            $(document).ready(function(){
                $('.mask-phone').inputmask('(99) 99999-9999', { "placeholder": "_" });
                $('.mask-cpf').inputmask('999.999.999-99', { "placeholder": "_" });
                // Máscara monetária simples
                $('.mask-money').inputmask('currency', {
                    prefix: 'R$ ',
                    groupSeparator: '.',
                    alias: 'numeric',
                    placeholder: '0',
                    autoGroup: true,
                    digits: 2,
                    digitsOptional: false,
                    clearMaskOnLostFocus: false,
                    rightAlign: false
                });
            });

            const form = document.getElementById('preAtendimentoForm');

            // Toggle Corretor
            const atSim = document.getElementById('atendido_sim');
            const atNao = document.getElementById('atendido_nao');
            const boxCorretor = document.getElementById('campoNomeCorretor');
            const inCorretor = document.getElementById('nome_corretor');
            function toggleC() {
                if(atSim.checked){ boxCorretor.classList.remove('hidden'); inCorretor.required=true; }
                else { boxCorretor.classList.add('hidden'); inCorretor.required=false; inCorretor.value=''; }
            }
            atSim.addEventListener('change', toggleC); atNao.addEventListener('change', toggleC);

            // Toggle Pré-Contrato & Scroll Suave
            const selCompra = document.getElementById('comprou_1o_lote');
            const secPre = document.getElementById('preContratoSection');
            function toggleP() {
                if(selCompra.value === 'Sim') {
                    secPre.classList.remove('hidden');
                    // Scroll Suave
                    setTimeout(() => {
                        secPre.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 100);
                }
                else {
                    secPre.classList.add('hidden');
                }
            }
            selCompra.addEventListener('change', toggleP); 

            // Canvas Assinatura
            const sigCv = document.getElementById('signatureCanvas'); const sigCtx = sigCv.getContext('2d');
            let drawing=false;
            function fitSig(){ sigCv.width=sigCv.offsetWidth; sigCv.height=sigCv.offsetHeight; sigCtx.lineWidth=2; sigCtx.strokeStyle="#263318"; }
            window.addEventListener('resize', fitSig); fitSig();
            const getPos=(e)=>{const r=sigCv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:t.clientX-r.left,y:t.clientY-r.top}};
            sigCv.addEventListener('mousedown',(e)=>{drawing=true;sigCtx.beginPath();sigCtx.moveTo(getPos(e).x,getPos(e).y)});
            sigCv.addEventListener('mousemove',(e)=>{if(drawing){sigCtx.lineTo(getPos(e).x,getPos(e).y);sigCtx.stroke()}});
            sigCv.addEventListener('mouseup',()=>drawing=false);
            sigCv.addEventListener('mouseleave',()=>drawing=false);
            sigCv.addEventListener('touchstart',(e)=>{drawing=true;sigCtx.beginPath();sigCtx.moveTo(getPos(e).x,getPos(e).y);e.preventDefault()});
            sigCv.addEventListener('touchmove',(e)=>{if(drawing){sigCtx.lineTo(getPos(e).x,getPos(e).y);sigCtx.stroke();e.preventDefault()}});
            sigCv.addEventListener('touchend',()=>drawing=false);
            document.getElementById('clearSignature').addEventListener('click',()=>{sigCtx.clearRect(0,0,sigCv.width,sigCv.height);document.getElementById('assinatura_base64').value=''});

            // Camera
            const vid=document.getElementById('videoPreview'); const photoCv=document.getElementById('photoCanvas'); const phCtx=photoCv.getContext('2d');
            const fotoInp=document.getElementById('foto_cliente_base64');
            phCtx.fillStyle='#f4f4f4'; phCtx.fillRect(0,0,photoCv.width,photoCv.height);
            document.getElementById('startWebcam').addEventListener('click',async()=>{
                try{vid.srcObject=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});vid.classList.remove('hidden');photoCv.classList.add('hidden');document.getElementById('takePhoto').classList.remove('hidden');document.getElementById('startWebcam').classList.add('hidden');document.getElementById('clearPhoto').classList.remove('hidden');}catch(e){Swal.fire('Erro', 'Erro ao acessar câmera: '+e, 'error')}
            });
            document.getElementById('takePhoto').addEventListener('click',()=>{
                photoCv.width=vid.videoWidth;photoCv.height=vid.videoHeight;phCtx.drawImage(vid,0,0);
                fotoInp.value=photoCv.toDataURL('image/jpeg',0.8);
                vid.classList.add('hidden');photoCv.classList.remove('hidden');
                vid.srcObject.getTracks().forEach(t=>t.stop());
                document.getElementById('takePhoto').classList.add('hidden');document.getElementById('startWebcam').classList.remove('hidden');
            });
            document.getElementById('clearPhoto').addEventListener('click',()=>{
                fotoInp.value=''; phCtx.clearRect(0,0,photoCv.width,photoCv.height); phCtx.fillStyle='#f4f4f4'; phCtx.fillRect(0,0,photoCv.width,photoCv.height);
                if(vid.srcObject)vid.srcObject.getTracks().forEach(t=>t.stop());
                vid.classList.add('hidden');photoCv.classList.remove('hidden');
                document.getElementById('startWebcam').classList.remove('hidden');document.getElementById('takePhoto').classList.add('hidden');document.getElementById('clearPhoto').classList.add('hidden');
            });

            // PDF
            document.getElementById('btnGerarPDF').addEventListener('click',()=>{
                const el=document.getElementById('fichaContainer');
                document.getElementById('pdfHeader').classList.remove('hidden');
                el.classList.add('pdf-mode');
                const btns=document.querySelectorAll('.btn-area button, .btn-acao-secundaria, #photoContainer button');
                btns.forEach(b=>b.style.display='none');
                
                // Mostrar alerta de carregamento
                Swal.fire({title: 'Gerando PDF...', allowOutsideClick: false, didOpen: () => { Swal.showLoading() }});

                html2pdf().set({margin:5,filename:'Ficha.pdf',image:{type:'jpeg',quality:0.95},html2canvas:{scale:2,useCORS:true},jsPDF:{unit:'mm',format:'a4'}}).from(el).save().then(()=>{
                    el.classList.remove('pdf-mode'); document.getElementById('pdfHeader').classList.add('hidden');
                    btns.forEach(b=>b.style.display='');
                    Swal.close();
                });
            });

            // Submit com SweetAlert
            form.addEventListener('submit', async(e)=>{
                e.preventDefault();
                document.getElementById('assinatura_base64').value=sigCv.toDataURL();
                
                // Loading
                Swal.fire({
                    title: 'Salvando Ficha...',
                    html: 'Por favor, aguarde o envio.',
                    allowOutsideClick: false,
                    didOpen: () => { Swal.showLoading() }
                });
                
                const fd=new FormData(form); const d={}; fd.forEach((v,k)=>d[k]=v);
                
                const refs=[]; for(let i=1;i<=5;i++){ if(d[`ref_nome_${i}`]||d[`ref_tel_${i}`]) refs.push(`${d[`ref_nome_${i}`]} - ${d[`ref_tel_${i}`]}`); }
                d.referencias_pc=refs.join('\\n');
                
                const fontes=fd.getAll('fonte_midia_pc'); d.fonte_midia_pc=fontes.join(', ');

                d.esteve_plantao=(d.esteve_plantao==='sim')?1:0;
                d.foi_atendido=(d.foi_atendido==='sim')?1:0;
                d.autoriza_transmissao=(d.autoriza_transmissao==='sim')?1:0;

                try{
                    const r=await fetch('/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
                    const res=await r.json();
                    if(res.success){
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso!',
                            text: 'Ficha salva corretamente.',
                            confirmButtonColor: '#8cc63f'
                        });
                        form.reset(); sigCtx.clearRect(0,0,sigCv.width,sigCv.height);
                        document.getElementById('clearPhoto').click();
                        // Esconde a área extra após reset
                        secPre.classList.add('hidden');
                        // Scroll topo
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    } else throw new Error(res.message);
                }catch(err){
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Falha ao salvar: ' + err.message
                    });
                }
            });
        });
    </script>
</body>
</html>
"""

# --- AUXILIARES ---
def formatar_telefone_n8n(telefone_bruto):
    try:
        numeros = ''.join(filter(str.isdigit, telefone_bruto))
        if 10 <= len(numeros) <= 11:
            return f"+55{numeros}"
        return None
    except:
        return None

# --- ROTAS ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not DATABASE_URL:
            return jsonify({'success': False, 'message': 'Banco de dados não configurado.'}), 500

        try:
            data = request.json
            nome = data.get('nome')
            cidade = data.get('cidade')
            telefone = formatar_telefone_n8n(data.get('telefone'))
            
            if not telefone or not nome:
                return jsonify({'success': False, 'message': 'Dados obrigatórios faltando.'}), 400

            campos = {
                'data_hora': datetime.datetime.now(datetime.timezone.utc),
                'nome': nome, 'telefone': telefone, 'rede_social': data.get('rede_social'),
                'abordagem_inicial': data.get('abordagem_inicial'),
                'esteve_plantao': to_bool_flag(data.get('esteve_plantao')),
                'foi_atendido': to_bool_flag(data.get('foi_atendido')),
                'nome_corretor': data.get('nome_corretor') if to_bool_flag(data.get('foi_atendido')) else None,
                'autoriza_transmissao': to_bool_flag(data.get('autoriza_transmissao')),
                'foto_cliente': data.get('foto_cliente_base64'),
                'assinatura': data.get('assinatura_base64'),
                'cidade': cidade, 'loteamento': data.get('loteamento'),
                'comprou_1o_lote': data.get('comprou_1o_lote'),
                'nivel_interesse': data.get('nivel_interesse'),
                
                'empreendimento_pc': data.get('empreendimento_pc'),
                'quadra_pc': data.get('quadra_pc'), 'lote_pc': data.get('lote_pc'),
                'm2_pc': data.get('m2_pc'), 'vl_m2_pc': data.get('vl_m2_pc'), 'vl_total_pc': data.get('vl_total_pc'),
                'venda_realizada_pc': data.get('venda_realizada_pc'),
                'forma_pagamento_pc': data.get('forma_pagamento_pc'),
                'entrada_forma_pagamento_pc': data.get('entrada_forma_pagamento_pc'),
                'numero_parcelas_pc': data.get('numero_parcelas_pc'),
                'vl_parcelas_pc': data.get('vl_parcelas_pc'),
                'vencimento_parcelas_pc': data.get('vencimento_parcelas_pc'),
                'nome_proponente_pc': data.get('nome_proponente_pc'),
                'rg_proponente_pc': data.get('rg_proponente_pc'),
                'orgao_emissor_proponente_pc': data.get('orgao_emissor_proponente_pc'),
                'cpf_proponente_pc': data.get('cpf_proponente_pc'),
                'estado_civil_pc': data.get('estado_civil_pc'),
                'filhos_pc': data.get('filhos_pc'),
                'endereco_pc': data.get('endereco_pc'),
                'tel_residencial_pc': data.get('tel_residencial_pc'),
                'celular_pc': data.get('celular_pc'), 'email_pc': data.get('email_pc'),
                'possui_residencia_pc': data.get('possui_residencia_pc'),
                'valor_aluguel_pc': data.get('valor_aluguel_pc'),
                'possui_financiamento_pc': data.get('possui_financiamento_pc'),
                'valor_financiamento_pc': data.get('valor_financiamento_pc'),
                'empresa_trabalha_pc': data.get('empresa_trabalha_pc'),
                'profissao_pc': data.get('profissao_pc'), 'tel_empresa_pc': data.get('tel_empresa_pc'),
                'renda_mensal_pc': data.get('renda_mensal_pc'),
                'nome_conjuge_pc': data.get('nome_conjuge_pc'),
                'rg_conjuge_pc': data.get('rg_conjuge_pc'),
                'orgao_emissor_conjuge_pc': data.get('orgao_emissor_conjuge_pc'),
                'cpf_conjuge_pc': data.get('cpf_conjuge_pc'),
                'tel_conjuge_pc': data.get('tel_conjuge_pc'), 'email_conjuge_pc': data.get('email_conjuge_pc'),
                'empresa_trabalha_conjuge_pc': data.get('empresa_trabalha_conjuge_pc'),
                'profissao_conjuge_pc': data.get('profissao_conjuge_pc'),
                'tel_empresa_conjuge_pc': data.get('tel_empresa_conjuge_pc'),
                'renda_mensal_conjuge_pc': data.get('renda_mensal_conjuge_pc'),
                'referencias_pc': data.get('referencias_pc'),
                'fonte_midia_pc': data.get('fonte_midia_pc')
            }

            cols = list(campos.keys())
            vals = list(campos.values())
            query = f"INSERT INTO atendimentos ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) RETURNING id"

            ticket_id = None
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, tuple(vals))
                    ticket_id = cursor.fetchone()[0]

            logger.info(f"✅ Ficha salva no Banco! ID: {ticket_id}")

            if N8N_WEBHOOK_URL:
                try:
                    payload_n8n = {
                        "ticket_id": ticket_id,
                        "nome": nome,
                        "telefone": telefone,
                        "nome_corretor": campos['nome_corretor'],
                        "cidade": cidade,
                        "timestamp": str(campos['data_hora'])
                    }
                    requests.post(N8N_WEBHOOK_URL, json=payload_n8n, timeout=2)
                except Exception as e:
                    logger.warning(f"Erro N8N: {e}")

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Erro POST: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS, corretores=OPCOES_CORRETORES)

@app.route('/avaliar', methods=['POST'])
def avaliar_atendimento():
    if not DATABASE_URL: return jsonify({'success': False}), 500
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or request.args.to_dict()
        if not data: return jsonify({'success': False}), 400
        
        ticket_id = data.get('ticket_id')
        nota = int(str(data.get('nota')).strip())
        
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE atendimentos SET nota_atendimento = %s WHERE id = %s", (nota, ticket_id))
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro avaliar: {e}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
