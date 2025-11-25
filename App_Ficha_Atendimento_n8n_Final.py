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

# --- CONFIGURAÇÕES DE PRODUÇÃO (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTA DE EMPREENDIMENTOS (Dropdown) ---
OPCOES_EMPREENDIMENTOS = [
    "Jardim dos Ipês",
    "Jardim Amazônia ET. 3",
    "Jardim Amazônia ET. 4",
    "Jardim Amazônia ET. 5",
    "Jardim Paulista",
    "Jardim Mato Grosso",
    "Jardim Florencia",
    "Benjamim Rossato",
    "Santa Felicidade",
    "Amazon Park",
    "Santa Fé",
    "Colina Verde",
    "Res. Terra de Santa Cruz",
    "Consórcio Gran Ville",
    "Consórcio Parque Cerrado",
    "Consórcio Recanto da Mata",
    "Jardim Vila Rica",
    "Jardim Amazônia Et. I",
    "Jardim Amazônia Et. II",
    "Loteamento Luxemburgo",
    "Loteamento Jardim Vila Bella",
    "Morada do Boque III",
    "Reserva Jardim",
    "Residencial Cidade Jardim",
    "Residencial Florais da Mata",
    "Residencial Jardim Imigrantes",
    "Residencial Vila Rica",
    "Residencial Vila Rica SINOP",
    "Outro / Não Listado"
]

# --- LISTA DE CORRETORES ---
OPCOES_CORRETORES = [
    "4083 - NEURA.T.PAVAN SINIGAGLIA",
    "2796 - PEDRO LAERTE RABECINI",
    "57 - Santos e Padilha Ltda - ME",
    "1376 - VALMIR MARIO TOMASI - SEGALA EMPREENDIMENTOS IMOBILIARIOS EIRELI",
    "1768 - SEGALA EMPREENDIMENTOS IMOBILIARIOS EIRELI",
    "2436 - PAULO EDUARDO GONCALVES DIAS",
    "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO",
    "4476 - Priscila Canhet da Silveira",
    "1531 - Walmir de Oliveira Queiroz",
    "4704 - MAYCON JEAN CAMPOS",
    "4084 - JAIMIR COMPAGNONI",
    "4096 - THAYANE APARECIDA BORGES 09648795908",
    "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA",
    "4587 - GABRIEL GALVÃO LOURENÃ‡O EMPREENDIMENTOS LTDA",
    "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR LTDA",
    "4868 - LENE ENGLER DA SILVA",
    "4087 - JOHNNY MIRANDA OJEDA 47447583120",
    "4531 - MG EMPREENDIMENTOS LTDA (MAIKON WILLIAN CHUSTA)",
    "4587 - GABRIEL GALVAO LOURENÃ‡O EMPREENDIMENTOS LTDA",
    "4826 - JEVIELI BELLO OLIVEIRA",
    "4825 - EVA VITORIA GALVAO LOURENCO",
    "54 - Ronaldo Padilha dos Santos",
    "1137 - Moacir Blemer Olivoto",
    "4872 - WQ CORRETORES LTDA (WALMIR QUEIROZ)",
    "720 - Luciane Bocchi ME",
    "5154 - FELIPE JOSE MOREIRA ALMEIDA",
    "3063 - SILVANA SEGALA",
    "2377 - Paulo Eduardo GonÃ§alves Dias",
    "Outro / Não Listado"
]

# --- BANCO DE DADOS (COM MIGRAÇÃO AUTOMÁTICA) ---
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
    migrations = [
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;"
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
        logger.info("✅ Banco de dados atualizado e pronto.")
    except Exception as e:
        logger.error(f"❌ Erro crítico ao inicializar Banco de Dados: {e}")

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

        .logo-text {
            font-weight: 800;
            letter-spacing: -0.05em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .logo-line {
            height: 4px;
            background-color: var(--cor-acento);
            width: 100px;
            margin: 0.5rem auto;
            border-radius: 2px;
        }

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
            letter-spacing: 0.05em;
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
            letter-spacing: 0.05em;
            margin-right: 10px;
        }
        .btn-pdf:hover { background-color: #f0f0f0; transform: translateY(-1px); }

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

        /* --- ESTILOS ESPECÍFICOS PARA O MODO PDF (FUNDO BRANCO) --- */
        .pdf-mode {
            background-color: #ffffff !important;
            border: 2px solid #263318 !important;
            box-shadow: none !important;
            color: #000000 !important;
            padding: 20px !important;
        }
        
        .pdf-mode h1, .pdf-mode h2 {
            color: #263318 !important; /* Mantém verde da marca no título */
            text-shadow: none !important;
        }
        
        .pdf-mode label, .pdf-mode span, .pdf-mode p {
            color: #000000 !important;
            font-weight: bold !important;
        }

        .pdf-mode .form-input, 
        .pdf-mode .form-textarea, 
        .pdf-mode .form-select {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #999 !important;
            box-shadow: none !important;
        }

        .pdf-mode .logo-text { color: #263318 !important; }
        
        /* Ajuste para canvas no PDF */
        .pdf-mode canvas {
            border: 1px solid #000 !important;
            background-color: #fff !important;
        }
        
        /* Ocultar placeholders de inputs vazios no PDF se desejar, ou manter */
        .pdf-mode ::placeholder { color: #ccc; }

        .hidden { display: none; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    
    <header class="w-full p-6 text-center">
        <h1 class="text-4xl md:text-5xl logo-text text-white">Araguaia</h1>
        <h2 class="text-xl md:text-2xl font-semibold text-white mt-1">Imóveis</h2>
        <div class="logo-line"></div>
        <p class="text-xs md:text-sm italic mt-2 tracking-wider" style="color: var(--cor-texto-cinza);">
            INVISTA EM SEUS SONHOS
        </p>
    </header>

    <main class="flex-grow flex items-center justify-center p-4">
        <div id="fichaContainer" class="form-container w-full max-w-4xl mx-auto p-6 md:p-10">
            
            <div id="pdfHeader" class="hidden text-center mb-6">
                <h1 class="text-3xl font-bold text-[#263318]">FICHA DE ATENDIMENTO</h1>
                <hr class="border-[#8cc63f] my-2">
            </div>

            <form id="preAtendimentoForm" class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                
                <div class="flex flex-col gap-5">
                    <div>
                        <label for="nome" class="block text-sm font-semibold mb-2 text-white">Nome do Cliente*</label>
                        <input type="text" id="nome" name="nome" class="form-input" placeholder="Nome Completo" required>
                    </div>
                    <div>
                        <label for="telefone" class="block text-sm font-semibold mb-2 text-white">Telefone / WhatsApp*</label>
                        <input type="tel" id="telefone" name="telefone" class="form-input" placeholder="(XX) XXXXX-XXXX" required>
                    </div>
                    <div>
                        <label for="rede_social" class="block text-sm font-semibold mb-2 text-gray-300">Instagram / Facebook</label>
                        <input type="text" id="rede_social" name="rede_social" class="form-input" placeholder="@usuario">
                    </div>
                    
                    <div>
                        <label for="cidade" class="block text-sm font-semibold mb-2 text-white">Cidade do Atendimento*</label>
                        <input type="text" id="cidade" name="cidade" class="form-input" required>
                    </div>
                    
                    <div>
                        <label for="loteamento" class="block text-sm font-semibold mb-2 text-white">Loteamento / Empreendimento</label>
                        <select id="loteamento" name="loteamento" class="form-select">
                            <option value="" disabled selected>Selecione uma opção...</option>
                            {% for opcao in empreendimentos %}
                                <option value="{{ opcao }}">{{ opcao }}</option>
                            {% endfor %}
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
                        <label for="nivel_interesse" class="block text-sm font-semibold mb-2 text-white">Nível de Interesse</label>
                        <select id="nivel_interesse" name="nivel_interesse" class="form-select">
                            <option value="Alto">Alto</option>
                            <option value="Médio">Médio</option>
                            <option value="Baixo">Baixo</option>
                        </select>
                    </div>
                </div>

                <div class="flex flex-col gap-5">
                    
                    <div class="p-4 rounded-lg bg-black/20 border border-white/10" id="photoContainer">
                        <label class="block text-sm font-semibold mb-3 text-white">Foto do Cliente</label>
                        <div class="flex flex-col items-center gap-3">
                            <div class="relative">
                                <canvas id="photoCanvas" class="photo-canvas w-32 h-32 rounded-full object-cover"></canvas>
                                <video id="videoPreview" class="video-preview w-32 h-32 rounded-full object-cover hidden" autoplay playsinline></video>
                            </div>
                            
                            <div class="flex flex-wrap justify-center gap-2" data-html2canvas-ignore="true">
                                <button type="button" id="startWebcam" class="text-xs bg-gray-700 text-white px-3 py-2 rounded hover:bg-gray-600 font-semibold uppercase">
                                    📷 Abrir Câmera
                                </button>
                                <button type="button" id="switchCamera" class="hidden text-xs bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-500 font-semibold uppercase">
                                    🔄 Inverter
                                </button>
                                <button type="button" id="takePhoto" class="hidden text-xs bg-green-600 text-white px-3 py-2 rounded hover:bg-green-500 font-semibold uppercase">
                                    📸 Capturar
                                </button>
                                <button type="button" id="clearPhoto" class="hidden text-xs text-red-400 underline">
                                    Remover
                                </button>
                            </div>
                        </div>
                        <input type="hidden" id="foto_cliente_base64" name="foto_cliente_base64">
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="block text-sm font-semibold mb-2 text-white">Já esteve em um plantão da Araguaia?*</span>
                            <div class="flex gap-4">
                                <label class="flex items-center cursor-pointer"><input type="radio" name="esteve_plantao" value="sim" class="accent-[#8cc63f]" required> <span class="ml-2">Sim</span></label>
                                <label class="flex items-center cursor-pointer"><input type="radio" name="esteve_plantao" value="nao" class="accent-[#8cc63f]"> <span class="ml-2">Não</span></label>
                            </div>
                        </div>

                        <div>
                            <span class="block text-sm font-semibold mb-2 text-white">Já possui corretor na Araguaia?*</span>
                            <div class="flex gap-4">
                                <label class="flex items-center cursor-pointer"><input type="radio" name="foi_atendido" value="sim" id="atendido_sim" class="accent-[#8cc63f]" required> <span class="ml-2">Sim</span></label>
                                <label class="flex items-center cursor-pointer"><input type="radio" name="foi_atendido" value="nao" id="atendido_nao" class="accent-[#8cc63f]"> <span class="ml-2">Não</span></label>
                            </div>
                        </div>
                        
                        <div id="campoNomeCorretor" class="hidden animate-fade-in p-3 bg-[#8cc63f]/10 border border-[#8cc63f] rounded-md">
                            <label for="nome_corretor" class="block text-sm font-bold mb-1 text-[#8cc63f]">Selecione o Corretor:</label>
                            <select id="nome_corretor" name="nome_corretor" class="form-select font-semibold">
                                <option value="" disabled selected>Selecione um corretor...</option>
                                {% for corretor in corretores %}
                                    <option value="{{ corretor }}">{{ corretor }}</option>
                                {% endfor %}
                            </select>
                        </div>

                        <div>
                            <span class="block text-sm font-semibold mb-2 text-white">Autoriza lista de transmissão?*</span>
                            <div class="flex gap-4">
                                <label class="flex items-center cursor-pointer"><input type="radio" name="autoriza_transmissao" value="sim" class="accent-[#8cc63f]" required> <span class="ml-2">Sim</span></label>
                                <label class="flex items-center cursor-pointer"><input type="radio" name="autoriza_transmissao" value="nao" class="accent-[#8cc63f]"> <span class="ml-2">Não</span></label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="md:col-span-2">
                    <label for="abordagem_inicial" class="block text-sm font-semibold mb-2 text-white">Observações / Abordagem Inicial</label>
                    <textarea id="abordagem_inicial" name="abordagem_inicial" rows="3" class="form-textarea" placeholder="Detalhes importantes sobre o atendimento..."></textarea>
                </div>

                <div class="md:col-span-2">
                    <label class="block text-sm font-semibold mb-2 text-white">Assinatura do Cliente</label>
                    <canvas id="signatureCanvas" class="signature-canvas w-full h-32 cursor-crosshair"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="flex justify-end mt-1" data-html2canvas-ignore="true">
                        <button type="button" id="clearSignature" class="btn-acao-secundaria">Limpar Assinatura</button>
                    </div>
                </div>

                <div class="md:col-span-2 flex flex-col md:flex-row justify-end items-center gap-4 mt-4 btn-area">
                    <span class="text-sm font-medium mr-auto" style="color: var(--cor-texto-cinza);" id="dataAtual">Sorriso/MT</span>
                    
                    <button type="button" id="btnGerarPDF" class="btn-pdf w-full md:w-auto shadow-lg">
                        📄 Baixar Cópia (PDF)
                    </button>

                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto shadow-lg hover:shadow-xl">
                        Salvar Ficha
                    </button>
                </div>

                <div id="statusMessage" class="md:col-span-2 text-center p-3 rounded font-bold hidden"></div>
            </form>
        </div>
    </main>

    <footer class="w-full p-6 text-center text-xs opacity-50">
        © <span id="currentYear"></span> Araguaia Imóveis. Todos os direitos reservados.
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const today = new Date();
            document.getElementById('dataAtual').innerText = `Sorriso/MT, ${today.toLocaleDateString('pt-BR')}`;
            document.getElementById('currentYear').innerText = today.getFullYear();
            const form = document.getElementById('preAtendimentoForm');
            const statusMessage = document.getElementById('statusMessage');

            // --- LÓGICA DO CAMPO CORRETOR ---
            const atendidoSim = document.getElementById('atendido_sim');
            const atendidoNao = document.getElementById('atendido_nao');
            const campoNome = document.getElementById('campoNomeCorretor');
            const inputNomeCorretor = document.getElementById('nome_corretor');
            
            function toggleCorretor() {
                if(atendidoSim.checked) {
                    campoNome.classList.remove('hidden');
                    inputNomeCorretor.required = true;
                } else {
                    campoNome.classList.add('hidden');
                    inputNomeCorretor.required = false;
                    inputNomeCorretor.value = '';
                }
            }
            atendidoSim.addEventListener('change', toggleCorretor);
            atendidoNao.addEventListener('change', toggleCorretor);

            // --- GERAÇÃO DE PDF (CONFIGURADO PARA FUNDO BRANCO) ---
            document.getElementById('btnGerarPDF').addEventListener('click', function() {
                const btnPdf = this;
                const originalText = btnPdf.innerText;
                const element = document.getElementById('fichaContainer');
                const pdfHeader = document.getElementById('pdfHeader');

                btnPdf.innerText = "Gerando...";
                btnPdf.disabled = true;

                // 1. Preparar o ambiente para PDF (Modo Impressão)
                element.classList.add('pdf-mode'); // Ativa o CSS de fundo branco
                pdfHeader.classList.remove('hidden'); // Mostra título interno
                
                // Ocultar botões
                const botoes = document.querySelectorAll('.btn-area button, .btn-acao-secundaria');
                botoes.forEach(b => b.style.opacity = '0');

                // 2. Configurações do html2pdf
                const opt = {
                    margin:       [10, 10, 10, 10],
                    filename:     'Ficha_Atendimento_Araguaia.pdf',
                    image:        { type: 'jpeg', quality: 0.98 },
                    // html2canvas configurado para branco e escala menor para caber melhor
                    html2canvas:  { scale: 2, useCORS: true, backgroundColor: '#ffffff', scrollX: 0, scrollY: 0 },
                    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
                };

                // 3. Gerar e Salvar
                html2pdf().set(opt).from(element).save().then(function(){
                    // 4. Restaurar o layout original (Modo Dark)
                    element.classList.remove('pdf-mode');
                    pdfHeader.classList.add('hidden');
                    botoes.forEach(b => b.style.opacity = '1');
                    btnPdf.innerText = originalText;
                    btnPdf.disabled = false;
                }).catch(function(err) {
                    alert("Erro ao gerar PDF: " + err);
                    element.classList.remove('pdf-mode');
                    pdfHeader.classList.add('hidden');
                    botoes.forEach(b => b.style.opacity = '1');
                    btnPdf.innerText = originalText;
                    btnPdf.disabled = false;
                });
            });

            // --- CÂMERA ---
            const video = document.getElementById('videoPreview');
            const photoCanvas = document.getElementById('photoCanvas');
            const photoCtx = photoCanvas.getContext('2d');
            const startWebcamBtn = document.getElementById('startWebcam');
            const takePhotoBtn = document.getElementById('takePhoto');
            const switchCameraBtn = document.getElementById('switchCamera');
            const clearPhotoBtn = document.getElementById('clearPhoto');
            const fotoHiddenInput = document.getElementById('foto_cliente_base64');
            let stream = null;
            let currentFacingMode = 'environment'; 

            function drawPlaceholder() {
                // Desenha placeholder neutro
                photoCtx.fillStyle = '#f4f4f4'; // Fundo claro para o placeholder
                photoCtx.fillRect(0, 0, photoCanvas.width, photoCanvas.height);
                photoCtx.strokeStyle = '#ccc';
                photoCtx.strokeRect(0, 0, photoCanvas.width, photoCanvas.height);
                photoCtx.fillStyle = '#8cc63f';
                photoCtx.beginPath();
                photoCtx.arc(photoCanvas.width/2, photoCanvas.height/2 - 10, 20, 0, Math.PI*2);
                photoCtx.fill();
                photoCtx.beginPath();
                photoCtx.arc(photoCanvas.width/2, photoCanvas.height + 10, 40, 0, Math.PI*2);
                photoCtx.fill();
            }
            drawPlaceholder();

            async function startCamera() {
                if (stream) stream.getTracks().forEach(track => track.stop());
                try {
                    const constraints = { video: { facingMode: currentFacingMode }, audio: false };
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    video.srcObject = stream;
                    video.classList.remove('hidden');
                    photoCanvas.classList.add('hidden');
                    takePhotoBtn.classList.remove('hidden');
                    switchCameraBtn.classList.remove('hidden');
                    clearPhotoBtn.classList.remove('hidden');
                    startWebcamBtn.classList.add('hidden');
                } catch (err) {
                    alert("Erro ao acessar a câmera. Verifique permissões HTTPS.");
                }
            }

            startWebcamBtn.addEventListener('click', () => startCamera());
            switchCameraBtn.addEventListener('click', () => {
                currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
                startCamera();
            });

            takePhotoBtn.addEventListener('click', () => {
                photoCanvas.width = video.videoWidth;
                photoCanvas.height = video.videoHeight;
                if(currentFacingMode === 'user') {
                    photoCtx.translate(photoCanvas.width, 0);
                    photoCtx.scale(-1, 1);
                }
                photoCtx.drawImage(video, 0, 0);
                if(currentFacingMode === 'user') photoCtx.setTransform(1, 0, 0, 1, 0, 0);
                fotoHiddenInput.value = photoCanvas.toDataURL('image/jpeg', 0.8);
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                switchCameraBtn.classList.add('hidden');
                if(stream) stream.getTracks().forEach(t => t.stop());
            });

            clearPhotoBtn.addEventListener('click', () => {
                drawPlaceholder();
                fotoHiddenInput.value = '';
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                startWebcamBtn.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                switchCameraBtn.classList.add('hidden');
                clearPhotoBtn.classList.add('hidden');
                if(stream) stream.getTracks().forEach(t => t.stop());
            });

            // --- ASSINATURA ---
            const sigCanvas = document.getElementById('signatureCanvas');
            const sigCtx = sigCanvas.getContext('2d');
            let drawing = false;

            function resizeCanvas() {
                const rect = sigCanvas.getBoundingClientRect();
                sigCanvas.width = rect.width;
                sigCanvas.height = rect.height;
                // Ajuste de cor da assinatura para ser visível no dark mode e no pdf (verde escuro funciona bem em ambos)
                sigCtx.strokeStyle = "#263318"; 
                sigCtx.lineWidth = 2;
            }
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas(); 

            function getPos(e) {
                const rect = sigCanvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return { x: clientX - rect.left, y: clientY - rect.top };
            }

            function startDraw(e) {
                drawing = true;
                const pos = getPos(e);
                sigCtx.beginPath();
                sigCtx.moveTo(pos.x, pos.y);
                e.preventDefault();
            }

            function moveDraw(e) {
                if(!drawing) return;
                const pos = getPos(e);
                sigCtx.lineTo(pos.x, pos.y);
                sigCtx.stroke();
                e.preventDefault();
            }

            function endDraw(e) {
                if(drawing) {
                    sigCtx.stroke();
                    drawing = false;
                    document.getElementById('assinatura_base64').value = sigCanvas.toDataURL();
                }
            }

            sigCanvas.addEventListener('mousedown', startDraw);
            sigCanvas.addEventListener('mousemove', moveDraw);
            sigCanvas.addEventListener('mouseup', endDraw);
            sigCanvas.addEventListener('touchstart', startDraw);
            sigCanvas.addEventListener('touchmove', moveDraw);
            sigCanvas.addEventListener('touchend', endDraw);

            document.getElementById('clearSignature').addEventListener('click', () => {
                sigCtx.clearRect(0, 0, sigCanvas.width, sigCanvas.height);
                document.getElementById('assinatura_base64').value = '';
            });

            // --- ENVIO ---
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('saveButton');
                btn.disabled = true;
                btn.innerText = 'ENVIANDO...';

                const formData = new FormData(form);
                const data = {};
                formData.forEach((val, key) => data[key] = val);

                data.esteve_plantao = (data.esteve_plantao === 'sim') ? 1 : 0;
                data.foi_atendido = (data.foi_atendido === 'sim') ? 1 : 0;
                data.autoriza_transmissao = (data.autoriza_transmissao === 'sim') ? 1 : 0;
                data.foto_cliente_base64 = fotoHiddenInput.value;
                data.assinatura_base64 = document.getElementById('assinatura_base64').value;

                try {
                    const resp = await fetch('/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    const res = await resp.json();
                    
                    if(res.success) {
                        statusMessage.innerText = "FICHA SALVA COM SUCESSO!";
                        statusMessage.className = "md:col-span-2 text-center p-4 rounded bg-[#8cc63f] text-[#263318] shadow-lg animate-bounce";
                        statusMessage.classList.remove('hidden');
                        form.reset();
                        sigCtx.clearRect(0,0,sigCanvas.width, sigCanvas.height);
                        drawPlaceholder();
                        toggleCorretor();
                        statusMessage.scrollIntoView({ behavior: 'smooth' });
                    } else {
                        throw new Error(res.message);
                    }
                } catch (err) {
                    statusMessage.innerText = "ERRO: " + err.message;
                    statusMessage.className = "md:col-span-2 text-center p-4 rounded bg-red-500 text-white shadow-lg";
                    statusMessage.classList.remove('hidden');
                } finally {
                    btn.disabled = false;
                    btn.innerText = 'SALVAR FICHA';
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
            telefone_formatado = formatar_telefone_n8n(data.get('telefone'))
            
            if not telefone_formatado:
                return jsonify({'success': False, 'message': 'Telefone inválido.'}), 400
            if not nome or not cidade:
                return jsonify({'success': False, 'message': 'Nome e Cidade são obrigatórios.'}), 400

            rede_social = data.get('rede_social')
            abordagem_inicial = data.get('abordagem_inicial')
            loteamento = data.get('loteamento')
            comprou_1o_lote = data.get('comprou_1o_lote')
            nivel_interesse = data.get('nivel_interesse')
            esteve_plantao = data.get('esteve_plantao') == 1
            foi_atendido = data.get('foi_atendido') == 1
            nome_corretor = data.get('nome_corretor') if foi_atendido else None
            autoriza_transmissao = data.get('autoriza_transmissao') == 1
            foto_cliente_base64 = data.get('foto_cliente_base64')
            assinatura_base64 = data.get('assinatura_base64')
            data_hora = datetime.datetime.now(datetime.timezone.utc)

            insert_query = '''
                INSERT INTO atendimentos (
                    data_hora, nome, telefone, rede_social, abordagem_inicial, 
                    esteve_plantao, foi_atendido, nome_corretor, autoriza_transmissao, 
                    foto_cliente, assinatura,
                    cidade, loteamento, comprou_1o_lote, nivel_interesse
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            '''
            values = (
                data_hora, nome, telefone_formatado, rede_social, abordagem_inicial,
                esteve_plantao, foi_atendido, nome_corretor, autoriza_transmissao,
                foto_cliente_base64, assinatura_base64,
                cidade, loteamento, comprou_1o_lote, nivel_interesse
            )
            
            ticket_id = None
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_query, values)
                    result = cursor.fetchone()
                    if result:
                        ticket_id = result[0]
            
            logger.info(f"Ficha salva ID: {ticket_id}")

            if N8N_WEBHOOK_URL:
                try:
                    payload = {
                        "ticket_id": ticket_id,
                        "nome": nome,
                        "telefone": telefone_formatado,
                        "cidade": cidade,
                        "loteamento": loteamento,
                        "comprou_1o_lote": comprou_1o_lote,
                        "nivel_interesse": nivel_interesse,
                        "nome_corretor": nome_corretor,
                        "timestamp": str(data_hora)
                    }
                    requests.post(N8N_WEBHOOK_URL, json=payload, timeout=3)
                except Exception as e_n8n:
                    logger.warning(f"Erro N8N: {e_n8n}")
            
            return jsonify({'success': True, 'message': 'Sucesso!'})

        except Exception as e:
            logger.error(f"Erro POST: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS, corretores=OPCOES_CORRETORES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
