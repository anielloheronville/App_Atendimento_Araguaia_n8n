import flask
from flask import Flask, request, render_template_string, jsonify
import psycopg2
import os
import datetime
import requests
import logging
import json

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração da Aplicação ---
app = Flask(__name__)

def to_bool_flag(value):
    """Converte valores vindos do front/n8n para booleano."""
    if value is None: return False
    return str(value).strip().lower() in ('1', 'true', 'sim', 'yes')

def limpar_texto(texto):
    """Remove quebras de linha que quebram a exportação CSV."""
    if texto:
        return texto.replace('\n', ' - ').replace('\r', '')
    return texto

# --- CONFIGURAÇÕES DE PRODUÇÃO (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTAS ---
OPCOES_EMPREENDIMENTOS = ["Jardim dos Ipês", "Jardim Amazônia ET. 3", "Jardim Amazônia ET. 4", "Jardim Amazônia ET. 5", "Jardim Paulista", "Jardim Mato Grosso", "Jardim Florencia", "Benjamim Rossato", "Santa Felicidade", "Amazon Park", "Santa Fé", "Colina Verde", "Res. Terra de Santa Cruz", "Consórcio Gran Ville", "Consórcio Parque Cerrado", "Consórcio Recanto da Mata", "Jardim Vila Rica", "Jardim Amazônia Et. I", "Jardim Amazônia Et. II", "Loteamento Luxemburgo", "Loteamento Jardim Vila Bella", "Morada do Boque III", "Reserva Jardim", "Residencial Cidade Jardim", "Residencial Florais da Mata", "Residencial Jardim Imigrantes", "Residencial Vila Rica", "Residencial Vila Rica SINOP", "Outro / Não Listado"]

OPCOES_CORRETORES = ["4083 - NEURA.T.PAVAN SINIGAGLIA", "2796 - PEDRO LAERTE RABECINI", "57 - Santos e Padilha Ltda - ME", "1376 - VALMIR MARIO TOMASI", "1768 - SEGALA EMPREENDIMENTOS", "2436 - PAULO EDUARDO GONCALVES DIAS", "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO", "4476 - Priscila Canhet da Silveira", "1531 - Walmir de Oliveira Queiroz", "4704 - MAYCON JEAN CAMPOS", "4084 - JAIMIR COMPAGNONI", "4096 - THAYANE APARECIDA BORGES", "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA", "4587 - GABRIEL GALVÃO LOURENÇO", "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR", "4868 - LENE ENGLER DA SILVA", "4087 - JOHNNY MIRANDA OJEDA", "4531 - MG EMPREENDIMENTOS LTDA", "4826 - JEVIELI BELLO OLIVEIRA", "4825 - EVA VITORIA GALVAO LOURENCO", "54 - Ronaldo Padilha dos Santos", "1137 - Moacir Blemer Olivoto", "4872 - WQ CORRETORES LTDA", "720 - Luciane Bocchi ME", "5154 - FELIPE JOSE MOREIRA ALMEIDA", "3063 - SILVANA SEGALA", "2377 - Paulo Eduardo Gonçalves Dias", "Outro / Não Listado"]

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
    # Migrações - Incluindo os campos novos
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
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cep_pc TEXT;",
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
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS fonte_midia_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS outros_lotes_pc TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_outro_lote TEXT;"
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
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
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

        /* Estilo para erro de validação */
        .input-error {
            border-color: #ff4444 !important;
            box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.2) !important;
        }

        /* Títulos de Seção Estilizados (Tarja Verde com Ícone) */
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
        
        .section-icon { width: 1.2em; height: 1.2em; fill: currentColor; }

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
            touch-action: none; /* BLOQUEIA SCROLL NO MOBILE AO ASSINAR */
        }

        .btn-acao-secundaria {
            color: var(--cor-texto-cinza);
            font-size: 0.85rem;
            text-decoration: underline;
            cursor: pointer;
        }
        
        .hidden { display: none; }

        /* Busca Fixa */
        .search-container {
            background: rgba(0,0,0,0.3);
            border: 1px solid var(--cor-borda);
            border-radius: 0.5rem;
            padding: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        /* --- MODO PDF (ESTILO PAPEL) --- */
        .pdf-mode {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            border: none !important;
        }

        /* 1. Fonte Menor para Caber (Geral) */
        .pdf-mode, .pdf-mode * {
            font-size: 0.7rem !important; /* REDUÇÃO CRÍTICA DE FONTE */
        }

        .pdf-mode label, .pdf-mode span, .pdf-mode p, .pdf-mode h1, .pdf-mode h2, .pdf-mode h3, .pdf-mode div {
            color: #000000 !important;
            text-shadow: none !important;
        }

        .pdf-mode input, .pdf-mode textarea, .pdf-mode select {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 1px solid #333 !important;
            color: #000000 !important;
            padding: 0 5px !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }
        
        /* 2. Compactação dos Inputs e Margens */
        .pdf-mode .form-input, .pdf-mode .form-textarea, .pdf-mode .form-select {
             padding: 2px 5px !important;
             margin-bottom: 0px !important;
             height: auto !important;
        }
        .pdf-mode .mb-3 { margin-bottom: 0.2rem !important; }
        .pdf-mode .gap-5 { gap: 0.5rem !important; }
        .pdf-mode .pt-8 { padding-top: 1rem !important; }


        .pdf-mode .form-container, .pdf-mode .section-header, .pdf-mode #preContratoSection {
            border-color: #000000 !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }

        .pdf-mode .section-header {
            background-color: #e0e0e0 !important;
            color: #000 !important;
            border: 1px solid #000;
            padding: 0.4rem 1rem !important;
            font-size: 0.8rem !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.5rem !important;
        }

        .hide-on-pdf { display: none !important; }
        .pdf-mode .section-icon { fill: #000; }

        /* QUEBRA DE PÁGINA CRÍTICA */
        .pdf-mode #preContratoSection {
            page-break-before: always; /* FORÇA A NOVA PÁGINA: Ficha de Cadastro */
            margin-top: 0 !important;
        }

        .pdf-mode .grid, .pdf-mode .section-header, .pdf-mode .mb-3 { break-inside: avoid; }
        .pdf-mode .p-4, .pdf-mode .p-6, .pdf-mode .md\:p-10 { padding: 0 !important; }
        /* FIM DAS ALTERAÇÕES PARA PDF */
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
            
            <div id="searchBar" class="search-container">
                <span class="text-[#8cc63f] font-bold text-sm uppercase">Consultar Ficha:</span>
                <input type="number" id="inputBuscarId" placeholder="ID da Ficha" class="form-input" style="width: 120px; padding: 5px;">
                <button type="button" id="btnBuscar" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-sm font-bold">🔍 Buscar</button>
            </div>

            <div id="pdfHeader" class="hidden text-center mb-4">
                <h1 class="text-3xl font-bold text-black uppercase">Ficha de Atendimento / Pré-Contrato</h1>
                <hr class="border-black my-2">
            </div>

            <form id="preAtendimentoForm" class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                <input type="hidden" id="ficha_id" name="id" value=""> 
    
                <div class="flex flex-col gap-5">
                    <div><label class="block text-sm font-semibold mb-2 text-white">Nome do Cliente*</label><input type="text" id="nome" name="nome" class="form-input" required></div>
                    
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-white">Telefone / WhatsApp*</label>
                        <div class="flex items-center gap-2">
                            <input type="tel" id="telefone" name="telefone" class="form-input mask-phone" placeholder="(XX) XXXXX-XXXX" inputmode="tel" required>
                            <button type="button" id="btnZap" class="hide-on-pdf text-[#8cc63f] border border-[#8cc63f] p-2 rounded hover:bg-[#8cc63f] hover:text-[#263318] transition-colors hidden" title="Abrir no WhatsApp">
                                💬
                            </button>
                        </div>
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

                <div class="flex flex-col gap-5">
                    <div class="p-4 rounded-lg bg-black/20 border border-white/10" id="photoContainer">
                        <label class="block text-sm font-semibold mb-3 text-white">Foto do Cliente</label>
                        <div class="flex flex-col items-center gap-3">
                            <div class="relative">
                                <canvas id="photoCanvas" class="photo-canvas w-32 h-32 rounded-full object-cover"></canvas>
                                <img id="loadedPhoto" class="hidden w-32 h-32 rounded-full object-cover border-2 border-[#8cc63f]">
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
                            <label id="label_corretor" class="block text-sm font-bold mb-1 text-[#8cc63f]">Selecione o Corretor:</label>
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
                
                <div class="md:col-span-2 mt-4">
                    <label class="block text-sm font-semibold mb-2 text-white">Assinatura Digital (Canvas)</label>
                    <canvas id="sigCanvas" class="signature-canvas w-full h-32 cursor-crosshair bg-white/10"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="flex justify-end mt-1"><button type="button" id="clearSignature" class="btn-acao-secundaria">Limpar Assinatura</button></div>
                </div>

                <div id="preContratoSection" class="md:col-span-2 hidden border border-[var(--cor-acento)] rounded-lg p-6 bg-black/20 mt-4 transition-all duration-500">
                    <h2 class="text-2xl font-bold mb-4 text-[#8cc63f] text-center uppercase tracking-wide">Ficha de Cadastro - Pré-Contrato</h2>

                    <div class="section-header">
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg> Dados do Imóvel
                    </div>

                    <div class="mb-4 p-4 border border-[#8cc63f] rounded-md bg-[#8cc63f]/10 shadow-lg">
                         <span class="block text-sm font-extrabold text-[#8cc63f] mb-3 uppercase tracking-wider">⚡ Este cliente adquirirá MAIS DE UM LOTE neste empreendimento?</span>
                         <div class="flex gap-6">
                             <label class="flex items-center text-white cursor-pointer hover:text-[#8cc63f] transition bg-black/30 p-2 rounded w-full">
                                 <input type="radio" name="possui_outro_lote" value="Sim" class="accent-[#8cc63f] mr-3 scale-125"> 
                                 <span class="font-bold">SIM</span> 
                                 <span class="text-xs ml-2 opacity-70">(Habilitar cadastro sequencial)</span>
                             </label>
                             <label class="flex items-center text-white cursor-pointer hover:text-[#8cc63f] transition bg-black/30 p-2 rounded w-full">
                                 <input type="radio" name="possui_outro_lote" value="Não" class="accent-[#8cc63f] mr-3 scale-125" checked> 
                                 <span class="font-bold">NÃO</span>
                                 <span class="text-xs ml-2 opacity-70">(Apenas este lote)</span>
                             </label>
                         </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">Empreendimento</label><input type="text" name="empreendimento_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">QD</label><input type="text" name="quadra_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">LT</label><input type="text" name="lote_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">M²</label><input type="text" name="m2_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">VL. M²</label><input type="text" name="vl_m2_pc" class="form-input mask-money" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">VL. Total</label><input type="text" name="vl_total_pc" class="form-input mask-money" inputmode="numeric"></div>
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Corretor (Opcional)</label><input type="text" id="corretor_pc" class="form-input"></div>
                    </div>
                    <div class="mb-3">
                         <label class="block text-xs font-semibold mb-1 text-white">Observação sobre Outros Lotes (Ex: QD 10 LT 11 e 12):</label>
                         <input type="text" name="outros_lotes_pc" class="form-input" placeholder="Caso queira anotar aqui os outros lotes...">
                    </div>


                    <div class="section-header">
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M12.5 17.5h-4v-1.9c-1.3-.4-2.1-1.4-2.1-2.6 0-1.8 1.5-2.8 3.5-3.1v-2c-.9.1-1.6.5-1.9.9l-1.3-1c.6-.9 1.7-1.5 3.2-1.7V4h1.9v2c1.4.3 2.3 1.4 2.3 2.6 0 1.8-1.5 2.8-3.5 3.1v2.2c1.1-.1 1.9-.6 2.3-1.1l1.3 1c-.6 1.1-1.9 1.9-3.7 2.1v1.6z"/></svg> Forma de Pagamento
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

                    <div class="section-header">
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg> Dados do Proponente
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Nome</label><input type="text" name="nome_proponente_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">RG</label><input type="text" name="rg_proponente_pc" class="form-input" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Órgão Emissor</label><input type="text" name="orgao_emissor_proponente_pc" class="form-input"></div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div><label class="block text-xs font-semibold mb-1 text-white">CPF</label><input type="tel" name="cpf_proponente_pc" class="form-input mask-cpf" inputmode="numeric"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Estado Civil</label><input type="text" name="estado_civil_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Filhos</label><input type="text" name="filhos_pc" class="form-input"></div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div class="md:col-span-2">
                             <div class="grid grid-cols-3 gap-2">
                                 <div>
                                    <label class="block text-xs font-semibold mb-1 text-white">CEP</label>
                                    <div class="flex gap-2">
                                        <input type="text" id="cep_busca" name="cep_pc" class="form-input mask-cep" placeholder="00000-000">
                                        <button type="button" id="btnBuscarCep" class="hide-on-pdf bg-[#8cc63f] text-[#1a2610] px-3 rounded font-bold hover:bg-[#7ab82e] transition">🔎</button>
                                    </div>
                                 </div>
                                 <div class="col-span-2">
                                     <label class="block text-xs font-semibold mb-1 text-white">Endereço</label>
                                     <input type="text" name="endereco_pc" class="form-input">
                                 </div>
                             </div>
                        </div>
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
                            <label class="block text-xs font-semibold mb-1 text-white">Valor (R$)</label>
                            <input type="text" name="valor_financiamento_pc" class="form-input mask-money" inputmode="numeric">
                        </div>
                    </div>

                    <div class="section-header">
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg> Dados Profissionais
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Empresa</label><input type="text" name="empresa_trabalha_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Profissão</label><input type="text" name="profissao_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Empresa</label><input type="tel" name="tel_empresa_pc" class="form-input mask-phone" inputmode="tel"></div>
                    </div>
                    <div><label class="block text-xs font-semibold mb-1 text-white">Renda Mensal</label><input type="text" name="renda_mensal_pc" class="form-input w-full md:w-1/3 mask-money" inputmode="numeric"></div>

                    <div class="section-header">
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg> Dados do Cônjuge
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

                    <div class="section-header">Dados Profissionais do Cônjuge</div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div class="md:col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Empresa</label><input type="text" name="empresa_trabalha_conjuge_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Profissão</label><input type="text" name="profissao_conjuge_pc" class="form-input"></div>
                        <div><label class="block text-xs font-semibold mb-1 text-white">Tel. Empresa</label><input type="tel" name="tel_empresa_conjuge_pc" class="form-input mask-phone" inputmode="tel"></div>
                    </div>
                    <div><label class="block text-xs font-semibold mb-1 text-white">Renda Mensal</label><input type="text" name="renda_mensal_conjuge_pc" class="form-input w-full md:w-1/3 mask-money" inputmode="numeric"></div>

                    <div class="section-header">
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M12 12.75c1.63 0 3.07.39 4.24.9 1.08.48 1.76 1.56 1.76 2.73V18H6v-1.61c0-1.18.68-2.26 1.76-2.73 1.17-.52 2.61-.91 4.24-.91zM4 13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm1.13 1.1c-.37-.06-.74-.1-1.13-.1-2.21 0-4 1.79-4 4v2h4v-2c0-.81.25-1.56.64-2.19l.49.29zM19.13 14.1l.49-.29c.39.63.64 1.38.64 2.19v2h4v-2c0-2.21-1.79-4-4-4-.39 0-.76.04-1.13.1zM12 12c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3z"/></svg> Referências Comerciais e Pessoais
                    </div>
                    <div class="space-y-2 mb-4">
                        {% for i in range(1,6) %}
                        <div class="grid grid-cols-5 gap-2">
                            <div class="col-span-3"><label class="block text-xs font-semibold mb-1 text-white">Nome {{ i }}</label><input type="text" name="ref_nome_{{ i }}" class="form-input"></div>
                            <div class="col-span-2"><label class="block text-xs font-semibold mb-1 text-white">Tel. {{ i }}</label><input type="tel" name="ref_tel_{{ i }}" class="form-input mask-phone" inputmode="tel"></div>
                        </div>
                        {% endfor %}
                    </div>

                    <div class="section-header">
                        <svg class="section-icon" viewBox="0 0 24 24"><path d="M2 17h2v.5H3v1h1v.5H2v1h3v-4H2v1zm1 9h2v-.5H3v-1h1v-.5H2v-1h3v4H2v-1zm-1-9h2v-.5H2v-1h1v-.5H2v-1h3v4H2v-1zM7 9h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zm0 4h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zM7 4h2v-.5H7v-1h1v-.5H7v-1h3v4H7v-1zM12 2l-5 5H2v6h5l5 5V2zm0 0"/></svg> Fonte de Mídia
                    </div>
                    <div class="flex flex-wrap gap-3 mb-4">
                        {% for label, value in [('Placa','Placa'),('Jornal','Jornal'),('Site','Site'),('Outdoor','Outdoor'),('TV','TV'),('Panfleto','Panfleto'),('Indicação','Indicacao'),('Outros','Outros')] %}
                        <label class="flex items-center text-xs text-white"><input type="checkbox" name="fonte_midia_pc" value="{{ value }}" class="accent-[#8cc63f] mr-1"> {{ label }}</label>
                        {% endfor %}
                    </div>

                    <div class="section-header">
                         <svg class="section-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg> Condições Gerais
                    </div>
                    <div class="text-[0.7rem] leading-tight text-gray-200 mb-6 text-justify">
                        <p class="mb-2">1. O promitente comprador formaliza a intenção de adquirir o imóvel descrito acima de maneira irrevogável e irretratável...</p>
                        <p class="mb-2">2. A ausência da assinatura do Contrato de Compromisso de Venda e Compra do Imóvel pelo COMPRADOR no prazo estipulado...</p>
                        <p>3. Fica estipulado que o Foro da Comarca de Sorriso - MT será o competente para a resolução de quaisquer questões...</p>
                    </div>

                    <div class="mt-8 text-xs text-white">
                        <p class="mb-12 font-bold text-lg">De Acordo,</p>
                        
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-12 mb-12">
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

                <div class="md:col-span-2 flex flex-col md:flex-row justify-end items-center gap-4 mt-4 btn-area">
                    <button type="button" id="btnGerarPDF" class="btn-pdf w-full md:w-auto shadow-lg">📄 Baixar Cópia (PDF)</button>
                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto shadow-lg hover:shadow-xl">Salvar Ficha</button>
                </div>
            </form>
        </div>
    </main>
    <footer class="w-full p-6 text-center text-xs opacity-50">© 2024 Araguaia Imóveis.</footer>

    <script>
        $(document).ready(function(){
            
            // --- INICIALIZAÇÃO DAS MÁSCARAS ---
            $('.mask-phone').inputmask('(99) 99999-9999', { "placeholder": "_" });
            $('.mask-cpf').inputmask('999.999.999-99', { "placeholder": "_" });
            $('.mask-money').inputmask('currency', {prefix: 'R$ ', groupSeparator: '.', alias: 'numeric', placeholder: '0', autoGroup: true, digits: 2, digitsOptional: false, rightAlign: false});
            $('.mask-cep').inputmask('99999-999');

            // --- LÓGICA DE BUSCA DA FICHA (Backend Integration) ---
            $('#btnBuscar').click(async function(){
                const idFicha = $('#inputBuscarId').val();
                if(!idFicha) return Swal.fire('Atenção', 'Digite o ID da ficha para buscar.', 'warning');

                Swal.fire({title: 'Buscando Ficha...', didOpen:()=>{Swal.showLoading()}});

                try {
                    const resp = await fetch(`/buscar/${idFicha}`);
                    if(!resp.ok) throw new Error("Ficha não encontrada ou erro no servidor.");
                    const dados = await resp.json();

                    // 1. PREENCHE O ID OCULTO
                    $('#ficha_id').val(dados.id); 

                    $.each(dados, function(key, value) {
                        if(value === null || value === undefined) return;

                        if (['esteve_plantao', 'foi_atendido', 'autoriza_transmissao'].includes(key)) {
                            let isSim = (value === true || value === 'true' || value === 1);
                            let valStr = isSim ? 'sim' : 'nao';
                            $(`input[name="${key}"][value="${valStr}"]`).prop('checked', true);
                            $(`input[name="${key}"]:checked`).trigger('change');
                            return;
                        }

                        if(key === 'telefone') {
                            let num = value.replace(/\D/g, ''); 
                            if(num.startsWith('55') && num.length > 11) num = num.substring(2); 
                            $(`[name="${key}"]`).val(num);
                        } else {
                            let input = $(`[name="${key}"]`);
                            if (input.attr('type') === 'radio') {
                                $(`input[name="${key}"][value="${value}"]`).prop('checked', true);
                            } else {
                                input.val(value);
                            }
                        }
                        
                        if(key === 'fonte_midia_pc'){
                            const fontes = value.split(', ');
                            fontes.forEach(f => $(`input[name="fonte_midia_pc"][value="${f}"]`).prop('checked', true));
                        }
                    });

                    // --- SEGURANÇA VISUAL (FRONTEND) ---
                    // Trava os campos de Nome e Corretor
                    $('#nome').prop('readonly', true).addClass('bg-gray-800 text-gray-500 cursor-not-allowed border-red-900');
                    $('#nome_corretor').prop('disabled', true).addClass('bg-gray-800 text-gray-500 cursor-not-allowed border-red-900');
                    
                    if(dados.nome_corretor) {
                        $('#campoNomeCorretor').removeClass('hidden');
                    }
                    // -----------------------------------

                    if(dados.referencias_pc) {
                        const refs = dados.referencias_pc.split('\\n');
                        refs.forEach((ref, index) => {
                            if(ref.includes('-')) {
                                const parts = ref.split(' - ');
                                $(`[name="ref_nome_${index+1}"]`).val(parts[0].trim());
                                $(`[name="ref_tel_${index+1}"]`).val(parts[1].trim());
                            }
                        });
                    }

                    if(dados.foto_cliente) {
                        $('#loadedPhoto').attr('src', dados.foto_cliente).removeClass('hidden');
                        $('#photoCanvas, #videoPreview').addClass('hidden');
                        $('#foto_cliente_base64').val(dados.foto_cliente);
                        $('#clearPhoto').removeClass('hidden');
                        $('#startWebcam').addClass('hidden');
                    }

                    if(dados.assinatura) {
                        const img = new Image();
                        img.onload = function() { ctx.drawImage(img, 0, 0); };
                        img.src = dados.assinatura;
                        $('#assinatura_base64').val(dados.assinatura);
                    }

                    toggleP(); 
                    toggleC(); 
                    $('#telefone').trigger('input'); 

                    Swal.fire({icon: 'success', title: 'Ficha Carregada!', timer: 1500, showConfirmButton: false});

                } catch(err) {
                    Swal.fire('Erro', err.message, 'error');
                }
            });

            // --- BUSCA DE CEP AUTOMÁTICA ---
            $('#btnBuscarCep').click(async function(){
                let cep = $('#cep_busca').val().replace(/\D/g, '');
                if(cep.length !== 8) return Swal.fire('Erro', 'CEP inválido', 'error');
                
                Swal.fire({title: 'Buscando endereço...', didOpen:()=>{Swal.showLoading()}});
                
                try {
                    const res = await fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`);
                    if(!res.ok) throw new Error('CEP não encontrado');
                    const data = await res.json();
                    $('[name="endereco_pc"]').val(`${data.street}, ${data.neighborhood}`);
                    $('[name="cidade"]').val(data.city);
                    Swal.close();
                } catch(e) {
                    Swal.fire('Erro', 'Não foi possível buscar o CEP.', 'error');
                }
            });

            // --- BOTÃO WHATSAPP ---
            $('#telefone').on('input', function(){
                const val = $(this).val().replace(/\D/g, '');
                if(val.length >= 10) {
                    $('#btnZap').removeClass('hidden');
                } else {
                    $('#btnZap').addClass('hidden');
                }
            });

            $('#btnZap').click(function(){
                const num = $('#telefone').val().replace(/\D/g, '');
                if(num) window.open(`https://wa.me/55${num}`, '_blank');
            });


            // Toggle Corretor (ATUALIZADO PARA EXIBIR LISTA SEMPRE)
            const atSim = document.getElementById('atendido_sim');
            const atNao = document.getElementById('atendido_nao');
            const boxCorretor = document.getElementById('campoNomeCorretor');
            const inCorretor = document.getElementById('nome_corretor');
            const labelCorretor = document.getElementById('label_corretor');

            function toggleC() {
                // Se algum dos dois estiver marcado, mostra a caixa
                if(atSim.checked || atNao.checked) {
                    boxCorretor.classList.remove('hidden');
                    inCorretor.required = true;
                } else {
                    // Se nenhum estiver marcado (estado inicial)
                    boxCorretor.classList.add('hidden');
                    inCorretor.required = false;
                }

                if (atSim.checked) {
                    labelCorretor.innerText = "Indique seu corretor atual:*";
                } 
                else if (atNao.checked) {
                    labelCorretor.innerText = "Escolha um corretor para lhe atender:*";
                }
            }
            atSim.addEventListener('change', toggleC); 
            atNao.addEventListener('change', toggleC);


            // Toggle Pré-Contrato & Scroll Suave
            const selCompra = document.getElementById('comprou_1o_lote');
            const secPre = document.getElementById('preContratoSection');
            function toggleP() {
                const temDados = $('[name="empreendimento_pc"]').val() !== '';
                if(selCompra.value === 'Sim' || temDados) {
                    secPre.classList.remove('hidden');
                } else {
                    secPre.classList.add('hidden');
                }
            }
            selCompra.addEventListener('change', toggleP); 

            // Canvas Assinatura
            const cv = document.getElementById('sigCanvas'); const ctx = cv.getContext('2d');
            let drawing=false;
            function fitSig(){ cv.width=cv.offsetWidth; cv.height=cv.offsetHeight; ctx.lineWidth=2; ctx.strokeStyle="#fff"; }
            window.addEventListener('resize', fitSig); fitSig();
            const getPos=(e)=>{const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:t.clientX-r.left,y:t.clientY-r.top}};
            cv.addEventListener('mousedown',(e)=>{drawing=true;ctx.beginPath();ctx.moveTo(getPos(e).x,getPos(e).y)});
            cv.addEventListener('mousemove',(e)=>{if(drawing){ctx.lineTo(getPos(e).x,getPos(e).y);ctx.stroke()}});
            cv.addEventListener('mouseup',()=>drawing=false);
            cv.addEventListener('touchstart',(e)=>{drawing=true;ctx.beginPath();ctx.moveTo(getPos(e).x,getPos(e).y);e.preventDefault()});
            cv.addEventListener('touchmove',(e)=>{if(drawing){ctx.lineTo(getPos(e).x,getPos(e).y);ctx.stroke();e.preventDefault()}});
            cv.addEventListener('touchend',()=>drawing=false);
            $('#clearSignature').click(()=>{ ctx.clearRect(0,0,cv.width,cv.height); $('#assinatura_base64').val(''); });

            // Camera
            const v=document.getElementById('videoPreview'); const p=document.getElementById('photoCanvas'); const pc=p.getContext('2d');
            $('#startWebcam').click(async()=>{ 
                try{ v.srcObject = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}); 
                $(v).removeClass('hidden'); $(p).addClass('hidden'); $('#loadedPhoto').addClass('hidden'); 
                $('#takePhoto').removeClass('hidden'); $('#startWebcam').addClass('hidden'); $('#clearPhoto').removeClass('hidden'); }catch(e){Swal.fire('Erro', 'Camera: '+e, 'error')} 
            });
            $('#takePhoto').click(()=>{ 
                p.width=v.videoWidth; p.height=v.videoHeight; pc.drawImage(v,0,0); 
                $('#foto_cliente_base64').val(p.toDataURL('image/jpeg', 0.7));
                $(v).addClass('hidden'); $(p).removeClass('hidden'); 
                v.srcObject.getTracks().forEach(t=>t.stop());
                $('#takePhoto').addClass('hidden'); $('#startWebcam').removeClass('hidden');
            });
            $('#clearPhoto').click(()=>{
                $('#foto_cliente_base64').val(''); pc.clearRect(0,0,p.width,p.height); 
                $('#loadedPhoto').addClass('hidden').attr('src','');
                $(v).addClass('hidden'); $(p).removeClass('hidden');
                $('#startWebcam').removeClass('hidden'); $('#takePhoto').addClass('hidden'); $('#clearPhoto').addClass('hidden');
                if(v.srcObject) v.srcObject.getTracks().forEach(t=>t.stop());
            });

            // PDF
            $('#btnGerarPDF').click(function() {
                const element = document.getElementById('fichaContainer');
                const uiElements = $('.btn-area, .search-container, #photoContainer button, #clearSignature, #startWebcam, #takePhoto, #clearPhoto, .hide-on-pdf');
                
                $(element).addClass('pdf-mode'); 
                $('#pdfHeader').removeClass('hidden'); 
                uiElements.addClass('hidden'); 

                $('textarea').each(function() {
                    this.style.height = 'auto';
                    this.style.height = (this.scrollHeight + 5) + 'px';
                });

                if($('#comprou_1o_lote').val() === 'Sim' || $('[name="empreendimento_pc"]').val()) {
                    $('#preContratoSection').removeClass('hidden');
                }

                let nomeArq = $('#nome').val() || 'Cliente';
                nomeArq = nomeArq.replace(/[^a-z0-9]/gi, '_').toLowerCase();

                const opt = {
                    margin:       [10, 10, 10, 10],
                    filename:     `ficha_${nomeArq}.pdf`,
                    image:        { type: 'jpeg', quality: 0.98 },
                    html2canvas:  { scale: 2, useCORS: true, scrollY: 0, logging: false },
                    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
                    pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] } 
                };

                Swal.fire({title: 'Gerando PDF...', html: 'Aguarde...', allowOutsideClick: false, didOpen: () => { Swal.showLoading() }});

                html2pdf().set(opt).from(element).save().then(function() {
                    $(element).removeClass('pdf-mode');
                    $('#pdfHeader').addClass('hidden');
                    uiElements.removeClass('hidden');
                    $('textarea').css('height', ''); 
                    toggleP(); 
                    Swal.close();
                }).catch(err => {
                    console.error(err);
                    Swal.fire('Erro', 'Não foi possível gerar o PDF.', 'error');
                    $(element).removeClass('pdf-mode');
                    uiElements.removeClass('hidden');
                });
            });

            // Submit
            $('#preAtendimentoForm').submit(async function(e){
                e.preventDefault();

                let valid = true;
                $('[required]').each(function(){
                    if($(this).is(':visible') && !$(this).val()){
                        $(this).addClass('input-error');
                        valid = false;
                    } else {
                        $(this).removeClass('input-error');
                    }
                });

                if(!valid) {
                    Swal.fire('Atenção', 'Preencha os campos obrigatórios destacados em vermelho.', 'warning');
                    return;
                }

                $('#assinatura_base64').val(cv.toDataURL());
                Swal.fire({title:'Salvando...', allowOutsideClick:false, didOpen:()=>{Swal.showLoading()}});
                
                const fd = new FormData(this); const d = {}; fd.forEach((v,k)=>d[k]=v);
                
                const fontes = [];
                $('input[name="fonte_midia_pc"]:checked').each(function(){ fontes.push($(this).val()); });
                d.fonte_midia_pc = fontes.join(', ');

                const refs=[]; for(let i=1;i<=5;i++){ if(d[`ref_nome_${i}`]||d[`ref_tel_${i}`]) refs.push(`${d[`ref_nome_${i}`]} - ${d[`ref_tel_${i}`]}`); }
                d.referencias_pc=refs.join('\\n');

                d.esteve_plantao = $('input[name="esteve_plantao"]:checked').val() === 'sim' ? 1 : 0;
                d.foi_atendido = $('input[name="foi_atendido"]:checked').val() === 'sim' ? 1 : 0;
                d.autoriza_transmissao = $('input[name="autoriza_transmissao"]:checked').val() === 'sim' ? 1 : 0;
                
                // --- LÓGICA DE MÚLTIPLOS LOTES ---
                const isMultiplo = $('input[name="possui_outro_lote"]:checked').val() === 'Sim';

                try {
                    const r = await fetch('/', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
                    const res = await r.json();
                    
                    if(res.success){
                        
                        // LÓGICA NOVA: Se for múltiplo, oferece limpar apenas o lote
                        if(isMultiplo) {
                             Swal.fire({
                                title: 'Ficha Salva!', 
                                text: `ID: ${res.ticket_id}. Deseja manter os dados do cliente para cadastrar o PRÓXIMO LOTE?`, 
                                icon: 'success',
                                showCancelButton: true,
                                confirmButtonText: 'Sim, Próximo Lote',
                                cancelButtonText: 'Não, Finalizar',
                                confirmButtonColor: '#8cc63f'
                             }).then((result) => {
                                if (result.isConfirmed) {
                                    // Limpa apenas os dados do lote para nova inserção
                                    $('#ficha_id').val(''); // Garante novo ID
                                    $('[name="quadra_pc"], [name="lote_pc"], [name="m2_pc"], [name="vl_m2_pc"], [name="vl_total_pc"]').val('');
                                    $('[name="entrada_forma_pagamento_pc"], [name="vl_parcelas_pc"]').val('');
                                    // Rola a tela até a parte do imóvel
                                    document.getElementById('preContratoSection').scrollIntoView({ behavior: 'smooth' });
                                } else {
                                    window.location.reload();
                                }
                             });
                        } else {
                             Swal.fire('Sucesso!', `Ficha Salva! ID: ${res.ticket_id}`, 'success').then(()=>{
                                window.location.reload();
                            });
                        }

                    } else throw new Error(res.message);
                } catch(err) {
                    Swal.fire('Erro', err.message, 'error');
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
            
            # --- VERIFICA SE É EDIÇÃO OU NOVO ---
            record_id = data.get('id')  # Pega o ID do campo hidden se existir
            
            nome = data.get('nome')
            cidade = data.get('cidade')
            telefone = formatar_telefone_n8n(data.get('telefone'))
            
            if not telefone or not nome:
                return jsonify({'success': False, 'message': 'Dados obrigatórios faltando.'}), 400

            # Dicionário de Campos (Incluindo os novos campos de Lotes Extras)
            campos = {
                'data_hora': datetime.datetime.now(datetime.timezone.utc),
                'nome': nome, 
                'telefone': telefone, 
                'rede_social': data.get('rede_social'),
                'abordagem_inicial': limpar_texto(data.get('abordagem_inicial')), 
                'esteve_plantao': to_bool_flag(data.get('esteve_plantao')),
                'foi_atendido': to_bool_flag(data.get('foi_atendido')),
                'nome_corretor': data.get('nome_corretor'), # Salva corretor sempre
                'autoriza_transmissao': to_bool_flag(data.get('autoriza_transmissao')),
                'foto_cliente': data.get('foto_cliente_base64'),
                'assinatura': data.get('assinatura_base64'),
                'cidade': cidade, 
                'loteamento': data.get('loteamento'),
                'comprou_1o_lote': data.get('comprou_1o_lote'),
                'nivel_interesse': data.get('nivel_interesse'),
                'empreendimento_pc': data.get('empreendimento_pc'),
                'quadra_pc': data.get('quadra_pc'), 
                'lote_pc': data.get('lote_pc'),
                'm2_pc': data.get('m2_pc'), 
                'vl_m2_pc': data.get('vl_m2_pc'), 
                'vl_total_pc': data.get('vl_total_pc'),
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
                'cep_pc': data.get('cep_pc'),
                'endereco_pc': data.get('endereco_pc'),
                'tel_residencial_pc': data.get('tel_residencial_pc'),
                'celular_pc': data.get('celular_pc'), 
                'email_pc': data.get('email_pc'),
                'possui_residencia_pc': data.get('possui_residencia_pc'),
                'valor_aluguel_pc': data.get('valor_aluguel_pc'),
                'possui_financiamento_pc': data.get('possui_financiamento_pc'),
                'valor_financiamento_pc': data.get('valor_financiamento_pc'),
                'empresa_trabalha_pc': data.get('empresa_trabalha_pc'),
                'profissao_pc': data.get('profissao_pc'), 
                'tel_empresa_pc': data.get('tel_empresa_pc'),
                'renda_mensal_pc': data.get('renda_mensal_pc'),
                'nome_conjuge_pc': data.get('nome_conjuge_pc'),
                'rg_conjuge_pc': data.get('rg_conjuge_pc'),
                'orgao_emissor_conjuge_pc': data.get('orgao_emissor_conjuge_pc'),
                'cpf_conjuge_pc': data.get('cpf_conjuge_pc'),
                'tel_conjuge_pc': data.get('tel_conjuge_pc'), 
                'email_conjuge_pc': data.get('email_conjuge_pc'),
                'empresa_trabalha_conjuge_pc': data.get('empresa_trabalha_conjuge_pc'),
                'profissao_conjuge_pc': data.get('profissao_conjuge_pc'),
                'tel_empresa_conjuge_pc': data.get('tel_empresa_conjuge_pc'),
                'renda_mensal_conjuge_pc': data.get('renda_mensal_conjuge_pc'),
                'referencias_pc': limpar_texto(data.get('referencias_pc')), 
                'fonte_midia_pc': data.get('fonte_midia_pc'),
                'outros_lotes_pc': data.get('outros_lotes_pc'),   # Novo Campo
                'possui_outro_lote': data.get('possui_outro_lote') # Novo Campo
            }

            ticket_id = None
            
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    
                    if record_id:
                        # --- LÓGICA DE UPDATE ---
                        # Removemos data_hora do update para não alterar a data de criação original
                        campos_update = campos.copy()
                        del campos_update['data_hora'] 
                        
                        # --- SEGURANÇA BACKEND ---
                        # Removemos nome e corretor para impedir alteração via POST após criação (opcional, mas seguro)
                        if 'nome' in campos_update: 
                            del campos_update['nome']
                        if 'nome_corretor' in campos_update: 
                            del campos_update['nome_corretor']
                        # -----------------------------
                        
                        set_clause = ", ".join([f"{key} = %s" for key in campos_update.keys()])
                        vals = list(campos_update.values())
                        vals.append(record_id) # Adiciona o ID no final para o WHERE
                        
                        query = f"UPDATE atendimentos SET {set_clause} WHERE id = %s RETURNING id"
                        cur.execute(query, tuple(vals))
                        ticket_id = record_id 
                        logger.info(f"🔄 Ficha Atualizada! ID: {ticket_id}")
                        
                    else:
                        # --- LÓGICA DE INSERT ---
                        cols = list(campos.keys())
                        vals = list(campos.values())
                        query = f"INSERT INTO atendimentos ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) RETURNING id"
                        cur.execute(query, tuple(vals))
                        ticket_id = cur.fetchone()[0]
                        logger.info(f"✅ Nova Ficha criada! ID: {ticket_id}")

            if N8N_WEBHOOK_URL:
                 # Se houver webhook configurado, envia os dados (opcional)
                 # requests.post(N8N_WEBHOOK_URL, json={**campos, 'id': ticket_id})
                 pass

            return jsonify({'success': True, 'ticket_id': ticket_id})

        except Exception as e:
            logger.error(f"Erro POST: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS, corretores=OPCOES_CORRETORES)

# --- ROTA DE BUSCA DE FICHA ---
@app.route('/buscar/<int:id_ficha>', methods=['GET'])
def buscar_ficha(id_ficha):
    if not DATABASE_URL: return jsonify({'error': 'DB não configurado'}), 500
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM atendimentos WHERE id = %s", (id_ficha,))
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    row = cur.fetchone()
                    if not row: return jsonify({}), 404
                    data = dict(zip(columns, row))
                    # Converte datas para string para o JSON não quebrar
                    for k, v in data.items():
                        if isinstance(v, datetime.datetime): data[k] = v.isoformat()
                    return jsonify(data)
        return jsonify({}), 404
    except Exception as e:
        logger.error(f"Erro Busca: {e}")
        return jsonify({'error': str(e)}), 500

# --- ROTA DE AVALIAÇÃO (Opcional, se usar estrelas) ---
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
    # Roda a aplicação
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
