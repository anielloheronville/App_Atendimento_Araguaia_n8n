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
    if value is None: return False
    return str(value).strip().lower() in ('1', 'true', 'sim', 'yes')

# --- CONFIGURAÇÕES (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTAS ---
OPCOES_EMPREENDIMENTOS = ["Jardim dos Ipês", "Jardim Amazônia ET. 3", "Jardim Amazônia ET. 4", "Jardim Amazônia ET. 5", "Jardim Paulista", "Jardim Mato Grosso", "Jardim Florencia", "Benjamim Rossato", "Santa Felicidade", "Amazon Park", "Santa Fé", "Colina Verde", "Res. Terra de Santa Cruz", "Consórcio Gran Ville", "Consórcio Parque Cerrado", "Consórcio Recanto da Mata", "Jardim Vila Rica", "Jardim Amazônia Et. I", "Jardim Amazônia Et. II", "Loteamento Luxemburgo", "Loteamento Jardim Vila Bella", "Morada do Boque III", "Reserva Jardim", "Residencial Cidade Jardim", "Residencial Florais da Mata", "Residencial Jardim Imigrantes", "Residencial Vila Rica", "Residencial Vila Rica SINOP", "Outro / Não Listado"]
OPCOES_CORRETORES = ["4083 - NEURA.T.PAVAN SINIGAGLIA", "2796 - PEDRO LAERTE RABECINI", "57 - Santos e Padilha Ltda - ME", "1376 - VALMIR MARIO TOMASI", "1768 - SEGALA EMPREENDIMENTOS", "2436 - PAULO EDUARDO GONCALVES DIAS", "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO", "4476 - Priscila Canhet da Silveira", "1531 - Walmir de Oliveira Queiroz", "4704 - MAYCON JEAN CAMPOS", "4084 - JAIMIR COMPAGNONI", "4096 - THAYANE APARECIDA BORGES", "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA", "4587 - GABRIEL GALVÃO LOURENÇO", "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR", "4868 - LENE ENGLER DA SILVA", "4087 - JOHNNY MIRANDA OJEDA", "4531 - MG EMPREENDIMENTOS LTDA", "4826 - JEVIELI BELLO OLIVEIRA", "4825 - EVA VITORIA GALVAO LOURENCO", "54 - Ronaldo Padilha dos Santos", "1137 - Moacir Blemer Olivoto", "4872 - WQ CORRETORES LTDA", "720 - Luciane Bocchi ME", "5154 - FELIPE JOSE MOREIRA ALMEIDA", "3063 - SILVANA SEGALA", "2377 - Paulo Eduardo Gonçalves Dias", "Outro / Não Listado"]

# --- BANCO DE DADOS ---
def init_db():
    if not DATABASE_URL: return
    create_table_query = '''CREATE TABLE IF NOT EXISTS atendimentos (id SERIAL PRIMARY KEY, data_hora TIMESTAMPTZ NOT NULL, nome TEXT NOT NULL, telefone TEXT NOT NULL, rede_social TEXT, abordagem_inicial TEXT, esteve_plantao BOOLEAN, foi_atendido BOOLEAN, nome_corretor TEXT, autoriza_transmissao BOOLEAN, foto_cliente TEXT, assinatura TEXT, cidade TEXT, loteamento TEXT)'''
    # Migrações completas
    migrations = [
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nota_atendimento INTEGER DEFAULT 0;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empreendimento_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS quadra_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS lote_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS m2_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_m2_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_total_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS venda_realizada_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS forma_pagamento_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS entrada_forma_pagamento_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS numero_parcelas_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vl_parcelas_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vencimento_parcelas_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nome_proponente_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS rg_proponente_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS orgao_emissor_proponente_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cpf_proponente_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS estado_civil_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS filhos_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS endereco_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_residencial_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS celular_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS email_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_residencia_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_aluguel_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_financiamento_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_financiamento_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empresa_trabalha_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS profissao_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_empresa_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS renda_mensal_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nome_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS rg_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS orgao_emissor_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cpf_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS email_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empresa_trabalha_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS profissao_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tel_empresa_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS renda_mensal_conjuge_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS referencias_pc TEXT;", "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS fonte_midia_pc TEXT;"
    ]
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        for m in migrations:
            try: cursor.execute(m)
            except: pass
        conn.close()
    except Exception as e: logger.error(f"Erro DB: {e}")

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
        :root { --cor-bg-fundo: #263318; --cor-bg-form: #324221; --cor-acento: #8cc63f; --cor-texto-claro: #ffffff; --cor-borda: #4a5e35; }
        body { background-color: var(--cor-bg-fundo); color: var(--cor-texto-claro); font-family: 'Montserrat', sans-serif; }
        .form-container { background-color: var(--cor-bg-form); border-radius: 0.75rem; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); border: 1px solid var(--cor-borda); }
        
        .section-header { width: 100%; background-color: var(--cor-acento); color: #1a2610; font-weight: 800; text-transform: uppercase; padding: 0.6rem 1rem; border-radius: 0.375rem; margin-top: 1.5rem; margin-bottom: 1rem; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem; }
        .section-icon { width: 1.2em; height: 1.2em; fill: currentColor; }
        
        .form-input, .form-textarea, .form-select { background-color: #263318; border: 1px solid var(--cor-borda); color: var(--cor-texto-claro); border-radius: 0.5rem; padding: 0.75rem; width: 100%; }
        .btn-salvar { background-color: var(--cor-acento); color: #1a2610; font-weight: 800; padding: 0.85rem 2rem; border-radius: 0.5rem; cursor: pointer; text-transform: uppercase; }
        .btn-pdf { background-color: #ffffff; color: #263318; font-weight: 700; padding: 0.85rem 1.5rem; border-radius: 0.5rem; cursor: pointer; text-transform: uppercase; margin-right: 10px; }
        .signature-canvas, .photo-canvas, .video-preview { border: 2px dashed var(--cor-borda); border-radius: 0.5rem; background-color: rgba(0,0,0,0.2); }
        .search-container { background: rgba(0,0,0,0.3); border: 1px solid var(--cor-borda); border-radius: 0.5rem; padding: 10px; margin-bottom: 20px; display: flex; gap: 10px; align-items: center; }
        .hidden { display: none; }

        /* --- PDF MODE FIXES --- */
        .pdf-mode {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 20px !important;
            font-size: 12px !important;
        }
        /* Força TODOS os textos a serem pretos no PDF */
        .pdf-mode * { color: #000000 !important; border-color: #000 !important; }
        .pdf-mode .form-input, .pdf-mode .form-textarea, .pdf-mode .form-select {
            background-color: #ffffff !important;
            border: 1px solid #000 !important;
        }
        .pdf-mode .section-header {
            background-color: #e5e7eb !important; /* Cinza claro */
            color: #000 !important;
            border: 1px solid #000;
        }
        .pdf-mode .section-icon { fill: #000 !important; }
        
        /* Remove o Grid no PDF para evitar cortes, empilha tudo */
        .pdf-mode .grid { display: block !important; }
        .pdf-mode .col-span-2, .pdf-mode .md\:col-span-2, .pdf-mode .md\:col-span-3, .pdf-mode .md\:col-span-4 { width: 100% !important; display: block !important; margin-bottom: 10px !important; }
        .pdf-mode input, .pdf-mode select { margin-bottom: 5px !important; }
        
        /* Garante que a seção extra apareça */
        .pdf-mode #preContratoSection { display: block !important; opacity: 1 !important; max-height: none !important; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <header class="w-full p-6 text-center">
        <h1 class="text-4xl md:text-5xl font-extrabold text-white">Araguaia</h1>
        <h2 class="text-xl md:text-2xl font-semibold text-white mt-1">Imóveis</h2>
        <div class="h-1 bg-[#8cc63f] w-24 mx-auto mt-2 rounded"></div>
    </header>

    <main class="flex-grow flex items-center justify-center p-4">
        <div id="fichaContainer" class="form-container w-full max-w-4xl mx-auto p-6 md:p-10">
            
            <!-- BUSCA -->
            <div id="searchBar" class="search-container">
                <span class="text-[#8cc63f] font-bold text-sm uppercase">Consultar Ficha:</span>
                <input type="number" id="inputBuscarId" placeholder="ID" class="form-input" style="width: 100px; padding: 5px;">
                <button type="button" id="btnBuscar" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-sm font-bold">🔍 Buscar</button>
            </div>

            <div id="pdfHeader" class="hidden text-center mb-4">
                <h1 class="text-2xl font-bold uppercase">Ficha de Atendimento / Pré-Contrato</h1>
                <hr class="border-black my-2">
            </div>

            <form id="preAtendimentoForm">
                <!-- CABEÇALHO -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="flex flex-col gap-4">
                        <div><label class="block text-xs font-bold mb-1 text-white">Nome do Cliente*</label><input type="text" name="nome" id="nome" class="form-input" required></div>
                        <div><label class="block text-xs font-bold mb-1 text-white">Telefone*</label><input type="tel" name="telefone" class="form-input mask-phone" required></div>
                        <div><label class="block text-xs font-bold mb-1 text-white">Cidade*</label><input type="text" name="cidade" class="form-input" required></div>
                        <div><label class="block text-xs font-bold mb-1 text-white">Loteamento</label>
                            <select name="loteamento" class="form-select">
                                <option value="" disabled selected>Selecione...</option>
                                {% for op in empreendimentos %}<option value="{{ op }}">{{ op }}</option>{% endfor %}
                            </select>
                        </div>
                        <div><label class="block text-xs font-bold mb-1 text-[#8cc63f]">Realizou compra do 1º Lote?</label>
                            <select id="comprou_1o_lote" name="comprou_1o_lote" class="form-select border-[#8cc63f]" required>
                                <option value="" disabled selected>Selecione...</option><option value="Sim">Sim</option><option value="Não">Não</option>
                            </select>
                        </div>
                        <div><label class="block text-xs font-bold mb-1 text-white">Interesse</label>
                            <select name="nivel_interesse" class="form-select"><option>Alto</option><option>Médio</option><option>Baixo</option></select>
                        </div>
                    </div>

                    <div class="flex flex-col gap-4">
                        <div class="p-2 rounded bg-black/20 border border-white/10" id="photoContainer">
                            <label class="block text-xs font-bold mb-1 text-white">Foto</label>
                            <div class="flex flex-col items-center gap-2">
                                <canvas id="photoCanvas" class="photo-canvas w-24 h-24 rounded-full object-cover bg-gray-200"></canvas>
                                <img id="loadedPhoto" class="hidden w-24 h-24 rounded-full object-cover border-2 border-[#8cc63f]">
                                <video id="videoPreview" class="video-preview w-24 h-24 rounded-full object-cover hidden" autoplay playsinline></video>
                                <div class="flex gap-2 text-xs" data-html2canvas-ignore="true">
                                    <button type="button" id="startWebcam" class="bg-gray-700 px-2 py-1 rounded text-white">📷 Abrir</button>
                                    <button type="button" id="takePhoto" class="hidden bg-green-600 px-2 py-1 rounded text-white">📸 Capturar</button>
                                    <button type="button" id="clearPhoto" class="hidden text-red-400 underline">X</button>
                                </div>
                            </div>
                            <input type="hidden" id="foto_cliente_base64" name="foto_cliente_base64">
                        </div>
                        <div class="space-y-2 text-sm text-white">
                            <div><span class="font-bold">Esteve em plantão?</span>
                                <div class="flex gap-4"><label><input type="radio" name="esteve_plantao" value="sim" class="accent-[#8cc63f]"> Sim</label><label><input type="radio" name="esteve_plantao" value="nao" class="accent-[#8cc63f]"> Não</label></div>
                            </div>
                            <div><span class="font-bold">Possui corretor?</span>
                                <div class="flex gap-4"><label><input type="radio" name="foi_atendido" value="sim" id="at_sim" class="accent-[#8cc63f]"> Sim</label><label><input type="radio" name="foi_atendido" value="nao" id="at_nao" class="accent-[#8cc63f]"> Não</label></div>
                            </div>
                            <div id="boxCorretor" class="hidden"><select id="nome_corretor" name="nome_corretor" class="form-select text-xs">{% for c in corretores %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select></div>
                            <div><span class="font-bold">Autoriza lista?</span>
                                <div class="flex gap-4"><label><input type="radio" name="autoriza_transmissao" value="sim" class="accent-[#8cc63f]"> Sim</label><label><input type="radio" name="autoriza_transmissao" value="nao" class="accent-[#8cc63f]"> Não</label></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4"><label class="block text-xs font-bold mb-1 text-white">Observações</label><textarea name="abordagem_inicial" rows="2" class="form-textarea"></textarea></div>

                <!-- PRÉ-CONTRATO -->
                <div id="preContratoSection" class="hidden bg-black/20 p-4 rounded border border-[#8cc63f] mt-4">
                    <h2 class="text-xl font-bold text-[#8cc63f] text-center mb-4 uppercase">Dados Complementares</h2>

                    <div class="section-header"><svg class="section-icon" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg> Imóvel</div>
                    <div class="grid grid-cols-4 gap-2 mb-2">
                        <input type="text" name="quadra_pc" placeholder="QD" class="form-input">
                        <input type="text" name="lote_pc" placeholder="LT" class="form-input">
                        <input type="text" name="m2_pc" placeholder="M²" class="form-input">
                        <input type="text" name="vl_total_pc" placeholder="Total R$" class="form-input mask-money" inputmode="numeric">
                    </div>

                    <div class="section-header"><svg class="section-icon" viewBox="0 0 24 24"><path d="M12.5 17.5h-4v-1.9c-1.3-.4-2.1-1.4-2.1-2.6 0-1.8 1.5-2.8 3.5-3.1v-2c-.9.1-1.6.5-1.9.9l-1.3-1c.6-.9 1.7-1.5 3.2-1.7V4h1.9v2c1.4.3 2.3 1.4 2.3 2.6 0 1.8-1.5 2.8-3.5 3.1v2.2c1.1-.1 1.9-.6 2.3-1.1l1.3 1c-.6 1.1-1.9 1.9-3.7 2.1v1.6z"/></svg> Pagamento</div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-2 text-white text-xs">
                         <div class="flex gap-4"><label><input type="radio" name="venda_realizada_pc" value="Estabelecimento"> Estabelecimento</label><label><input type="radio" name="venda_realizada_pc" value="Telefone"> Telefone</label></div>
                         <input type="text" name="entrada_forma_pagamento_pc" placeholder="Entrada / Condição" class="form-input">
                         <input type="text" name="vl_parcelas_pc" placeholder="Valor Parcela" class="form-input mask-money" inputmode="numeric">
                    </div>

                    <div class="section-header"><svg class="section-icon" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg> Proponente</div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
                        <input type="text" name="nome_proponente_pc" placeholder="Nome Completo" class="form-input md:col-span-2">
                        <input type="tel" name="cpf_proponente_pc" placeholder="CPF" class="form-input mask-cpf" inputmode="numeric">
                        <input type="text" name="rg_proponente_pc" placeholder="RG" class="form-input">
                        <input type="text" name="orgao_emissor_proponente_pc" placeholder="Org. Emissor" class="form-input">
                        <input type="text" name="estado_civil_pc" placeholder="Est. Civil" class="form-input">
                        <input type="text" name="endereco_pc" placeholder="Endereço" class="form-input md:col-span-3">
                        <div class="md:col-span-3 flex gap-4 text-white text-xs items-center mt-2">
                            <span>Financiamento:</span>
                            <label><input type="radio" name="possui_financiamento_pc" value="Nao" class="accent-[#8cc63f]"> Não</label>
                            <label><input type="radio" name="possui_financiamento_pc" value="Veiculos" class="accent-[#8cc63f]"> Veículos</label>
                            <input type="text" name="valor_financiamento_pc" placeholder="Valor R$" class="form-input w-24 mask-money" inputmode="numeric">
                        </div>
                    </div>

                    <div class="section-header"><svg class="section-icon" viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg> Profissional</div>
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <input type="text" name="empresa_trabalha_pc" placeholder="Empresa" class="form-input">
                        <input type="text" name="profissao_pc" placeholder="Profissão" class="form-input">
                        <input type="text" name="renda_mensal_pc" placeholder="Renda" class="form-input mask-money">
                    </div>

                    <div class="section-header"><svg class="section-icon" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg> Cônjuge</div>
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <input type="text" name="nome_conjuge_pc" placeholder="Nome" class="form-input md:col-span-2">
                        <input type="tel" name="cpf_conjuge_pc" placeholder="CPF" class="form-input mask-cpf">
                    </div>

                    <div class="section-header">Assinaturas</div>
                    <div class="grid grid-cols-2 gap-10 text-center text-xs mt-8 mb-4 text-white">
                        <div class="border-t border-white pt-2">COMPRADOR</div>
                        <div class="border-t border-white pt-2">CORRETOR</div>
                    </div>
                </div>

                <div class="mt-4">
                    <label class="block text-xs font-bold mb-2 text-white">Assinatura Digital</label>
                    <canvas id="sigCanvas" class="signature-canvas w-full h-32 cursor-crosshair bg-white/10"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="text-right"><button type="button" id="limparSig" class="text-xs underline text-gray-300">Limpar</button></div>
                </div>

                <div class="flex justify-end gap-3 mt-6 btn-area">
                     <button type="button" id="btnPDF" class="btn-pdf shadow">📄 PDF</button>
                     <button type="submit" class="btn-salvar shadow">SALVAR FICHA</button>
                </div>
            </form>
        </div>
    </main>

    <script>
        $(document).ready(function(){
            $('.mask-phone').inputmask('(99) 99999-9999'); $('.mask-cpf').inputmask('999.999.999-99');
            $('.mask-money').inputmask('currency', {prefix:'R$ ', groupSeparator:'.', alias:'numeric', digits:2, rightAlign:false});
            
            // Lógica
            $('#comprou_1o_lote').change(function(){
                if($(this).val() == 'Sim') { $('#preContratoSection').removeClass('hidden'); }
                else { $('#preContratoSection').addClass('hidden'); }
            });
            $('#at_sim').change(function(){ $('#boxCorretor').removeClass('hidden'); }); $('#at_nao').change(function(){ $('#boxCorretor').addClass('hidden'); });

            // Assinatura
            const cv=document.getElementById('sigCanvas'); const ctx=cv.getContext('2d'); let drawing=false;
            function fit(){cv.width=cv.offsetWidth;cv.height=cv.offsetHeight;ctx.lineWidth=2;ctx.strokeStyle="#fff";} window.addEventListener('resize', fit); fit();
            const getPos=(e)=>{const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:t.clientX-r.left,y:t.clientY-r.top}};
            cv.addEventListener('mousedown',(e)=>{drawing=true;ctx.beginPath();ctx.moveTo(getPos(e).x,getPos(e).y)});
            cv.addEventListener('mousemove',(e)=>{if(drawing){ctx.lineTo(getPos(e).x,getPos(e).y);ctx.stroke()}});
            cv.addEventListener('mouseup',()=>drawing=false); cv.addEventListener('touchstart',(e)=>{drawing=true;ctx.beginPath();ctx.moveTo(getPos(e).x,getPos(e).y);e.preventDefault()});
            cv.addEventListener('touchmove',(e)=>{if(drawing){ctx.lineTo(getPos(e).x,getPos(e).y);ctx.stroke();e.preventDefault()}});
            $('#limparSig').click(()=>{ctx.clearRect(0,0,cv.width,cv.height);});

            // Camera
            const v=document.getElementById('videoPreview');const p=document.getElementById('photoCanvas');const pc=p.getContext('2d');
            $('#startWebcam').click(async()=>{try{v.srcObject=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});$(v).removeClass('hidden');$(p).addClass('hidden');$('#loadedPhoto').addClass('hidden');$('#takePhoto').removeClass('hidden');$('#startWebcam').addClass('hidden');$('#clearPhoto').removeClass('hidden');}catch(e){Swal.fire('Erro',e,'error')}});
            $('#takePhoto').click(()=>{p.width=v.videoWidth;p.height=v.videoHeight;pc.drawImage(v,0,0);$('#foto_cliente_base64').val(p.toDataURL('image/jpeg',0.7));$(v).addClass('hidden');$(p).removeClass('hidden');v.srcObject.getTracks().forEach(t=>t.stop());$('#takePhoto').addClass('hidden');$('#startWebcam').removeClass('hidden');});
            $('#clearPhoto').click(()=>{ $('#foto_cliente_base64').val(''); pc.clearRect(0,0,p.width,p.height); $('#loadedPhoto').addClass('hidden'); $(v).addClass('hidden'); $(p).removeClass('hidden'); $('#startWebcam').removeClass('hidden'); $('#takePhoto').addClass('hidden'); $('#clearPhoto').addClass('hidden'); if(v.srcObject)v.srcObject.getTracks().forEach(t=>t.stop()); });

            // BUSCA INTELIGENTE (Preenche e Abre a Ficha)
            $('#btnBuscar').click(async function(){
                const id = $('#inputBuscarId').val();
                if(!id) return Swal.fire('Ops', 'Digite o ID', 'warning');
                Swal.fire({title:'Buscando...', didOpen:()=>{Swal.showLoading()}});
                try{
                    const r = await fetch(`/buscar/${id}`);
                    if(!r.ok) throw new Error('Não encontrado');
                    const d = await r.json();
                    
                    // 1. Limpa o form primeiro
                    $('#preAtendimentoForm')[0].reset();
                    $('#preContratoSection').addClass('hidden');

                    // 2. Preenche campos
                    $.each(d, (k,v)=>{
                        if(!v) return;
                        $(`[name="${k}"]`).val(v);
                        $(`input[name="${k}"][value="${v}"]`).prop('checked',true);
                        // Checkbox multiplo (fonte midia)
                        if(k==='fonte_midia_pc'){ v.split(', ').forEach(f=>$(`input[name="fonte_midia_pc"][value="${f}"]`).prop('checked',true)); }
                    });

                    // 3. Força abertura da área extra SE necessário
                    if(d.comprou_1o_lote === 'Sim') {
                        $('#preContratoSection').removeClass('hidden');
                    }

                    // 4. Imagens
                    if(d.foto_cliente){ $('#loadedPhoto').attr('src', d.foto_cliente).removeClass('hidden'); $('#photoCanvas').addClass('hidden'); $('#foto_cliente_base64').val(d.foto_cliente); }
                    if(d.assinatura){ const img=new Image(); img.onload=()=>{ctx.drawImage(img,0,0)}; img.src=d.assinatura; $('#assinatura_base64').val(d.assinatura); }

                    Swal.fire({icon:'success', title:'Carregado!', timer:1000, showConfirmButton:false});
                }catch(e){ Swal.fire('Erro', e.message, 'error'); }
            });

            // PDF GERAÇÃO (FIXED)
            $('#btnGerarPDF').click(()=>{
                const el=document.getElementById('fichaContainer');
                $('#pdfHeader').removeClass('hidden'); 
                $(el).addClass('pdf-mode'); // Ativa CSS de cor preta e block layout
                $('.btn-area, .search-container, #photoContainer button, #limparSig').hide(); // Esconde botoes
                
                Swal.fire({title:'Gerando PDF...', allowOutsideClick:false, didOpen:()=>{Swal.showLoading()}});
                html2pdf().set({
                    margin: 5, 
                    filename: `ficha_${$('#nome').val()||'cliente'}.pdf`, 
                    image: {type:'jpeg', quality:0.98},
                    html2canvas: {scale: 2, useCORS: true}, 
                    jsPDF: {unit:'mm', format:'a4'}
                }).from(el).save().then(()=>{
                    $(el).removeClass('pdf-mode'); 
                    $('#pdfHeader').addClass('hidden');
                    $('.btn-area, .search-container, #photoContainer button, #limparSig').show(); 
                    Swal.close();
                });
            });

            // Envio
            $('#preAtendimentoForm').submit(async function(e){
                e.preventDefault(); $('#assinatura_base64').val(cv.toDataURL());
                Swal.fire({title:'Salvando...', didOpen:()=>{Swal.showLoading()}});
                const fd=new FormData(this); const d={}; fd.forEach((v,k)=>d[k]=v);
                
                // Trata checkboxes
                const fontes=[]; $('input[name="fonte_midia_pc"]:checked').each(function(){fontes.push($(this).val())}); d.fonte_midia_pc=fontes.join(', ');
                d.esteve_plantao=$('input[name="esteve_plantao"]:checked').val()==='sim';
                d.foi_atendido=$('input[name="foi_atendido"]:checked').val()==='sim';
                d.autoriza_transmissao=$('input[name="autoriza_transmissao"]:checked').val()==='sim';

                try{
                    const r=await fetch('/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
                    const res=await r.json();
                    if(res.success) Swal.fire('Salvo!', `ID da Ficha: ${res.ticket_id}`, 'success');
                    else throw new Error(res.message);
                }catch(err){Swal.fire('Erro',err.message,'error');}
            });
        });
    </script>
</body>
</html>
"""

# ... (ROTAS PERMANECEM AS MESMAS DO ANTERIOR, JÁ ESTÃO COMPLETAS) ...
# Para economizar espaço, as rotas index, buscar_ficha e avaliar_atendimento são idênticas ao código anterior e devem ser mantidas aqui.
# Vou replicá-las abaixo apenas para garantir integridade se copiar/colar tudo.

# --- AUX ---
def formatar_telefone_n8n(telefone_bruto):
    try:
        numeros = ''.join(filter(str.isdigit, telefone_bruto))
        if 10 <= len(numeros) <= 11: return f"+55{numeros}"
        return None
    except: return None

# --- ROTAS ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not DATABASE_URL: return jsonify({'success': False, 'message': 'DB error'}), 500
        try:
            data = request.json
            campos = {
                'data_hora': datetime.datetime.now(datetime.timezone.utc),
                'nome': data.get('nome'), 'telefone': formatar_telefone_n8n(data.get('telefone')),
                'rede_social': data.get('rede_social'), 'abordagem_inicial': data.get('abordagem_inicial'),
                'esteve_plantao': data.get('esteve_plantao'), 'foi_atendido': data.get('foi_atendido'),
                'nome_corretor': data.get('nome_corretor'), 'autoriza_transmissao': data.get('autoriza_transmissao'),
                'foto_cliente': data.get('foto_cliente_base64'), 'assinatura': data.get('assinatura_base64'),
                'cidade': data.get('cidade'), 'loteamento': data.get('loteamento'),
                'comprou_1o_lote': data.get('comprou_1o_lote'), 'nivel_interesse': data.get('nivel_interesse'),
                # Pré-Contrato Completo
                'empreendimento_pc': data.get('empreendimento_pc'), 'quadra_pc': data.get('quadra_pc'), 'lote_pc': data.get('lote_pc'), 'm2_pc': data.get('m2_pc'), 'vl_total_pc': data.get('vl_total_pc'), 'vl_m2_pc': data.get('vl_m2_pc'),
                'venda_realizada_pc': data.get('venda_realizada_pc'), 'entrada_forma_pagamento_pc': data.get('entrada_forma_pagamento_pc'), 'vl_parcelas_pc': data.get('vl_parcelas_pc'), 'numero_parcelas_pc': data.get('numero_parcelas_pc'), 'vencimento_parcelas_pc': data.get('vencimento_parcelas_pc'),
                'nome_proponente_pc': data.get('nome_proponente_pc'), 'cpf_proponente_pc': data.get('cpf_proponente_pc'), 'rg_proponente_pc': data.get('rg_proponente_pc'), 'orgao_emissor_proponente_pc': data.get('orgao_emissor_proponente_pc'), 'estado_civil_pc': data.get('estado_civil_pc'), 'endereco_pc': data.get('endereco_pc'), 'possui_financiamento_pc': data.get('possui_financiamento_pc'), 'valor_financiamento_pc': data.get('valor_financiamento_pc'), 'valor_aluguel_pc': data.get('valor_aluguel_pc'),
                'empresa_trabalha_pc': data.get('empresa_trabalha_pc'), 'profissao_pc': data.get('profissao_pc'), 'tel_empresa_pc': data.get('tel_empresa_pc'), 'renda_mensal_pc': data.get('renda_mensal_pc'),
                'nome_conjuge_pc': data.get('nome_conjuge_pc'), 'cpf_conjuge_pc': data.get('cpf_conjuge_pc'), 'rg_conjuge_pc': data.get('rg_conjuge_pc'), 'orgao_emissor_conjuge_pc': data.get('orgao_emissor_conjuge_pc'), 'tel_conjuge_pc': data.get('tel_conjuge_pc'), 'email_conjuge_pc': data.get('email_conjuge_pc'),
                'empresa_trabalha_conjuge_pc': data.get('empresa_trabalha_conjuge_pc'), 'profissao_conjuge_pc': data.get('profissao_conjuge_pc'), 'tel_empresa_conjuge_pc': data.get('tel_empresa_conjuge_pc'), 'renda_mensal_conjuge_pc': data.get('renda_mensal_conjuge_pc'),
                'referencias_pc': data.get('referencias_pc'), 'fonte_midia_pc': data.get('fonte_midia_pc')
            }
            cols = list(campos.keys()); vals = list(campos.values())
            query = f"INSERT INTO atendimentos ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) RETURNING id"
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, tuple(vals))
                    tid = cur.fetchone()[0]
            if N8N_WEBHOOK_URL:
                try: requests.post(N8N_WEBHOOK_URL, json={'ticket_id': tid, 'nome': campos['nome'], 'telefone': campos['telefone'], 'corretor': campos['nome_corretor']}, timeout=2)
                except: pass
            return jsonify({'success': True, 'ticket_id': tid})
        except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500
    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS, corretores=OPCOES_CORRETORES)

@app.route('/buscar/<int:id_ficha>', methods=['GET'])
def buscar_ficha(id_ficha):
    if not DATABASE_URL: return jsonify({'error': 'DB error'}), 500
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM atendimentos WHERE id = %s", (id_ficha,))
                if cur.description:
                    cols = [desc[0] for desc in cur.description]
                    row = cur.fetchone()
                    if not row: return jsonify({}), 404
                    data = dict(zip(cols, row))
                    for k,v in data.items():
                        if isinstance(v, datetime.datetime): data[k] = v.isoformat()
                    return jsonify(data)
        return jsonify({}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/avaliar', methods=['POST'])
def avaliar():
    if not DATABASE_URL: return jsonify({'success': False}), 500
    try:
        d = request.get_json(silent=True) or request.form.to_dict() or request.args.to_dict()
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as c: c.execute("UPDATE atendimentos SET nota_atendimento = %s WHERE id = %s", (int(d.get('nota')), d.get('ticket_id')))
        return jsonify({'success': True})
    except: return jsonify({'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
