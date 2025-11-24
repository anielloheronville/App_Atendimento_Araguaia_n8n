import flask
from flask import Flask, request, render_template_string, jsonify, Response
import psycopg2
import base64
import os
import datetime
import requests

# --- Configuração da Aplicação ---
app = Flask(__name__)

# --- CONFIGURAÇÕES DE PRODUÇÃO (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTA DE EMPREENDIMENTOS (Para o Dropdown) ---
OPCOES_EMPREENDIMENTOS = [
    "Lançamento - Reserva do Bosque",
    "Lançamento - Altavista Premium",
    "Residencial Araguaia (Disponível)",
    "Jardim dos Ipês (> 10 Lotes)",
    "Vale do Sol (> 10 Lotes)",
    "Outros"
]

# --- DADOS DO LOGO (STRING COMPLETA E CORRIGIDA) ---
LOGO_BASE64_STRING = (
    "/9j/4AAQSkZJRgABAQEAYABgAAD/4QAiRXhpZgAATU0AKgAAAAgAAQESAAMAAAABAAEAAAAAAAD/2wBDAAIBAQIBAQIB"
    "AQQCAQIEAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBgcLDAsKDAwL/2wBDAQICAgQDBAUD"
    "BgYFBAQGBQcFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU/8AAEQgB9AH0AwEi"
    "AAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUS"
    "ITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZ"
    "naGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5u"
    "fo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUS"
    "ITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFicKGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2Rl"
    "ZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OX"
    "m5+jp6vLz9PX29/j5+v/aAAwDAQACEQMRAD8A/v4ooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "KACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKK"
    "AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIC"
    "AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
)

# --- Banco de Dados ---
def init_db():
    """
    Cria a tabela do banco de dados PostgreSQL se ela não existir.
    """
    if not DATABASE_URL:
        print("⚠️ AVISO: DATABASE_URL não encontrada. O app não conseguirá salvar no banco.")
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
        loteamento TEXT,
        comprou_1o_lote TEXT,
        nivel_interesse TEXT
    )
    '''
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
                
                # Tenta adicionar colunas novas caso a tabela já exista (migração simples)
                try:
                    cursor.execute("ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;")
                    cursor.execute("ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;")
                except Exception as e_alter:
                    print(f"Nota: Colunas já existem ou erro ao alterar: {e_alter}")
                    
        print("✅ Banco de dados conectado e tabela verificada.")
    except Exception as e:
        print(f"❌ Erro ao conectar no Banco: {e}")

# --- Template HTML (LAYOUT COMPLETO + NOVOS CAMPOS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha de Pré Atendimento - Araguaia Imóveis</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Cores personalizadas baseadas no design */
        :root {
            --cor-bg-fundo: #2d333b;
            --cor-bg-form: #3a414c;
            --cor-bg-titulo: #4f463c;
            --cor-botao-verde: #84cc16;
            --cor-texto-claro: #e0e0e0;
            --cor-texto-medio: #b0b0b0;
            --cor-borda: #5a616c;
        }
        body {
            background-color: var(--cor-bg-fundo);
            color: var(--cor-texto-claro);
            font-family: 'Inter', sans-serif;
        }
        .form-container {
            background-color: var(--cor-bg-form);
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .form-title {
            background-color: var(--cor-bg-titulo);
            border-top-left-radius: 0.5rem;
            border-top-right-radius: 0.5rem;
        }
        .form-input, .form-textarea, .form-select {
            background-color: #5a616c;
            border: 1px solid var(--cor-borda);
            color: var(--cor-texto-claro);
            border-radius: 0.375rem;
            padding: 0.75rem;
            width: 100%;
        }
        .form-input::placeholder, .form-textarea::placeholder {
            color: var(--cor-texto-medio);
        }
        .form-radio-label {
            color: var(--cor-texto-medio);
            margin-left: 0.5rem;
        }
        .btn-salvar {
            background-color: var(--cor-botao-verde);
            color: #2d333b;
            font-weight: bold;
            padding: 0.75rem 1.5rem;
            border-radius: 0.375rem;
            transition: all 0.2s;
        }
        .btn-salvar:hover {
            opacity: 0.85;
        }
        .btn-limpar {
            color: var(--cor-texto-medio);
            font-size: 0.875rem;
            text-decoration: underline;
            cursor: pointer;
        }
        .signature-canvas, .photo-canvas, .video-preview {
            border: 1px dashed var(--cor-borda);
            border-radius: 0.375rem;
            background-color: #5a616c;
        }
        /* Ocultar elementos */
        .hidden {
            display: none;
        }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <nav class="w-full bg-transparent p-4 md:p-6">
        <div class="container mx-auto flex justify-between items-center max-w-6xl">
            <img src="/logo.jpg" alt="Araguaia Imóveis" class="h-10 md:h-12">
            <span class="text-sm md:text-md" style="color: var(--cor-botao-verde);">
                INVISTA EM SEUS SONHOS
            </span>
        </div>
    </nav>

    <main class="flex-grow flex items-center justify-center p-4">
        <div class="form-container w-full max-w-4xl mx-auto">
            <div class="form-title p-4 text-center">
                <h2 class="text-xl font-semibold text-white">FICHA DE PRÉ ATENDIMENTO</h2>
            </div>

            <form id="preAtendimentoForm" class="p-6 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                
                <div class="flex flex-col gap-5">
                    <div>
                        <label for="nome" class="block text-sm font-medium mb-2">Nome*</label>
                        <input type="text" id="nome" name="nome" class="form-input" required>
                    </div>
                    <div>
                        <label for="telefone" class="block text-sm font-medium mb-2">Telefone*</label>
                        <input type="tel" id="telefone" name="telefone" class="form-input" placeholder="(XX) XXXXX-XXXX" required>
                    </div>
                    <div>
                        <label for="rede_social" class="block text-sm font-medium mb-2">Rede Social</label>
                        <input type="text" id="rede_social" name="rede_social" class="form-input">
                    </div>
                    
                    <div>
                        <label for="abordagem_inicial" class="block text-sm font-medium mb-2">Abordagem Inicial</label>
                        <textarea id="abordagem_inicial" name="abordagem_inicial" rows="3" class="form-textarea"></textarea>
                    </div>
                    
                    <div>
                        <label for="cidade" class="block text-sm font-medium mb-2">Cidade do Atendimento*</label>
                        <input type="text" id="cidade" name="cidade" class="form-input" required>
                    </div>
                    
                    <div>
                        <label for="loteamento" class="block text-sm font-medium mb-2">Loteamento / Empreendimento</label>
                        <select id="loteamento" name="loteamento" class="form-select">
                            <option value="" disabled selected>Selecione uma opção...</option>
                            {% for opcao in empreendimentos %}
                                <option value="{{ opcao }}">{{ opcao }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div>
                        <label for="comprou_1o_lote" class="block text-sm font-medium mb-2">Realizou o sonho da compra do 1º Lote?</label>
                        <select id="comprou_1o_lote" name="comprou_1o_lote" class="form-select" required>
                            <option value="" disabled selected>Selecione...</option>
                            <option value="Sim">Sim</option>
                            <option value="Não">Não</option>
                        </select>
                    </div>

                    <div>
                        <label for="nivel_interesse" class="block text-sm font-medium mb-2">Nível de Interesse</label>
                        <select id="nivel_interesse" name="nivel_interesse" class="form-select">
                            <option value="Alto">Alto</option>
                            <option value="Médio">Médio</option>
                            <option value="Baixo">Baixo</option>
                        </select>
                    </div>
                </div>

                <div class="flex flex-col gap-5">
                    <div>
                        <label class="block text-sm font-medium mb-2">Foto do Cliente</label>
                        <div class="flex items-center gap-4">
                            <canvas id="photoCanvas" class="photo-canvas w-24 h-24 rounded-full"></canvas>
                            <video id="videoPreview" class="video-preview w-24 h-24 rounded-full hidden" autoplay playsinline></video>
                            
                            <div class="flex flex-col gap-2">
                                <button type="button" id="startWebcam" class="text-sm text-white bg-blue-600 px-3 py-1 rounded hover:bg-blue-700">Abrir Câmera</button>
                                <button type="button" id="takePhoto" class="text-sm text-white bg-green-600 px-3 py-1 rounded hover:bg-green-700 hidden">Tirar Foto</button>
                                <button type="button" id="clearPhoto" class="text-sm text-gray-300 underline hidden">Limpar Foto</button>
                            </div>
                        </div>
                        <input type="hidden" id="foto_cliente_base64" name="foto_cliente_base64">
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="block text-sm font-medium mb-2">Já esteve em um dos plantões de atendimento da Araguaia Imóveis?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="esteve_plantao" value="sim" required> <span class="form-radio-label">Sim</span></label>
                                <label><input type="radio" name="esteve_plantao" value="nao"> <span class="form-radio-label">Não</span></label>
                            </div>
                        </div>

                        <div>
                            <span class="block text-sm font-medium mb-2">Já foi atendido por algum corretor?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="foi_atendido" value="sim" id="atendido_sim" required> <span class="form-radio-label">Sim</span></label>
                                <label><input type="radio" name="foi_atendido" value="nao" id="atendido_nao"> <span class="form-radio-label">Não</span></label>
                            </div>
                        </div>
                        
                        <div id="campoNomeCorretor" class="hidden">
                            <label for="nome_corretor" class="block text-sm font-medium mb-2">Se sim, qual o nome:</label>
                            <input type="text" id="nome_corretor" name="nome_corretor" class="form-input">
                        </div>

                        <div>
                            <span class="block text-sm font-medium mb-2">Autoriza a empresa Araguaia Imóveis te inserir na lista de transmissões de lançamentos?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="autoriza_transmissao" value="sim" required> <span class="form-radio-label">Sim</span></label>
                                <label><input type="radio" name="autoriza_transmissao" value="nao"> <span class="form-radio-label">Não</span></label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="md:col-span-2">
                    <label class="block text-sm font-medium mb-2">Assinatura do cliente</label>
                    <canvas id="signatureCanvas" class="signature-canvas w-full h-40"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="flex justify-between items-center mt-2">
                        <button type="button" id="clearSignature" class="btn-limpar">Limpar Assinatura</button>
                    </div>
                </div>

                <div class="md:col-span-2 flex flex-col md:flex-row justify-between items-center gap-4">
                    <span class="text-sm text-gray-300" id="dataAtual">Sorriso/MT, 10/11/2025</span>
                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto">Salvar Ficha</button>
                </div>

                <div id="statusMessage" class="md:col-span-2 text-center p-2 rounded hidden"></div>
                
            </form>
        </div>
    </main>

    <footer class="w-full p-4 mt-8">
        <div class="text-center text-xs text-gray-400">
            © <span id="currentYear">2025</span> Araguaia Imóveis. Todos os direitos reservados.
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            
            const form = document.getElementById('preAtendimentoForm');
            const statusMessage = document.getElementById('statusMessage');

            // --- DATA ATUAL ---
            const today = new Date();
            const dataFormatada = today.toLocaleDateString('pt-BR');
            document.getElementById('dataAtual').innerText = `Sorriso/MT, ${dataFormatada}`;
            document.getElementById('currentYear').innerText = today.getFullYear();

            // --- CÂMERA (FOTO DO CLIENTE) ---
            const video = document.getElementById('videoPreview');
            const photoCanvas = document.getElementById('photoCanvas');
            const photoCtx = photoCanvas.getContext('2d');
            const startWebcamBtn = document.getElementById('startWebcam');
            const takePhotoBtn = document.getElementById('takePhoto');
            const clearPhotoBtn = document.getElementById('clearPhoto');
            const fotoHiddenInput = document.getElementById('foto_cliente_base64');
            let stream = null;

            function drawAvatarPlaceholder() {
                photoCtx.fillStyle = '#b0b0b0';
                photoCtx.fillRect(0, 0, photoCanvas.width, photoCanvas.height);
                photoCtx.beginPath();
                photoCtx.arc(photoCanvas.width / 2, photoCanvas.height / 2.5, 20, 0, Math.PI * 2, true);
                photoCtx.fillStyle = '#e0e0e0';
                photoCtx.fill();
                photoCtx.beginPath();
                photoCtx.arc(photoCanvas.width / 2, photoCanvas.height + 30, 45, 0, Math.PI, false);
                photoCtx.fill();
            }
            drawAvatarPlaceholder();

            startWebcamBtn.addEventListener('click', async () => {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                    video.srcObject = stream;
                    video.classList.remove('hidden');
                    photoCanvas.classList.add('hidden');
                    takePhotoBtn.classList.remove('hidden');
                    clearPhotoBtn.classList.remove('hidden');
                    startWebcamBtn.classList.add('hidden');
                } catch (err) {
                    console.error("Erro ao acessar a câmera: ", err);
                    alert("Não foi possível acessar a câmera. Verifique as permissões.");
                }
            });

            takePhotoBtn.addEventListener('click', () => {
                photoCanvas.width = video.videoWidth;
                photoCanvas.height = video.videoHeight;
                photoCtx.drawImage(video, 0, 0, photoCanvas.width, photoCanvas.height);
                fotoHiddenInput.value = photoCanvas.toDataURL('image/jpeg', 0.8);
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
            });

            clearPhotoBtn.addEventListener('click', () => {
                photoCtx.clearRect(0, 0, photoCanvas.width, photoCanvas.height);
                drawAvatarPlaceholder();
                fotoHiddenInput.value = '';
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                startWebcamBtn.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                clearPhotoBtn.classList.add('hidden');
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
            });

            // --- CAMPO CONDICIONAL (NOME CORRETOR) ---
            const atendidoSim = document.getElementById('atendido_sim');
            const atendidoNao = document.getElementById('atendido_nao');
            const campoNomeCorretor = document.getElementById('campoNomeCorretor');
            const nomeCorretorInput = document.getElementById('nome_corretor');

            function toggleNomeCorretor() {
                if (atendidoSim.checked) {
                    campoNomeCorretor.classList.remove('hidden');
                    nomeCorretorInput.required = true;
                } else {
                    campoNomeCorretor.classList.add('hidden');
                    nomeCorretorInput.required = false;
                    nomeCorretorInput.value = ''; // Limpa o valor se 'Não' for marcado
                }
            }
            atendidoSim.addEventListener('change', toggleNomeCorretor);
            atendidoNao.addEventListener('change', toggleNomeCorretor);

            // --- ASSINATURA CANVAS ---
            const sigCanvas = document.getElementById('signatureCanvas');
            const sigCtx = sigCanvas.getContext('2d');
            const clearSignatureBtn = document.getElementById('clearSignature');
            const assinaturaHiddenInput = document.getElementById('assinatura_base64');
            let drawing = false;
            let dirty = false;

            function resizeCanvas() {
                const rect = sigCanvas.getBoundingClientRect();
                sigCanvas.width = rect.width;
                sigCanvas.height = rect.height;
            }
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();

            sigCtx.strokeStyle = "#FFFFFF";
            sigCtx.lineWidth = 2;

            function getMousePos(canvas, evt) {
                const rect = canvas.getBoundingClientRect();
                return { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
            }
            
            function getTouchPos(canvas, evt) {
                const rect = canvas.getBoundingClientRect();
                return { x: evt.touches[0].clientX - rect.left, y: evt.touches[0].clientY - rect.top };
            }

            function startDrawing(e) {
                drawing = true;
                dirty = true;
                const pos = e.touches ? getTouchPos(sigCanvas, e) : getMousePos(sigCanvas, e);
                sigCtx.beginPath();
                sigCtx.moveTo(pos.x, pos.y);
                e.preventDefault();
            }

            function draw(e) {
                if (!drawing) return;
                const pos = e.touches ? getTouchPos(sigCanvas, e) : getMousePos(sigCanvas, e);
                sigCtx.lineTo(pos.x, pos.y);
                sigCtx.stroke();
                e.preventDefault();
            }

            function stopDrawing(e) {
                if (drawing) {
                    sigCtx.stroke();
                    drawing = false;
                    assinaturaHiddenInput.value = sigCanvas.toDataURL('image/png');
                }
                e.preventDefault();
            }

            sigCanvas.addEventListener('mousedown', startDrawing);
            sigCanvas.addEventListener('mousemove', draw);
            sigCanvas.addEventListener('mouseup', stopDrawing);
            sigCanvas.addEventListener('mouseout', stopDrawing);
            sigCanvas.addEventListener('touchstart', startDrawing);
            sigCanvas.addEventListener('touchmove', draw);
            sigCanvas.addEventListener('touchend', stopDrawing);
            sigCanvas.addEventListener('touchcancel', stopDrawing);

            clearSignatureBtn.addEventListener('click', () => {
                sigCtx.clearRect(0, 0, sigCanvas.width, sigCanvas.height);
                assinaturaHiddenInput.value = '';
                dirty = false;
            });

            // --- ENVIO DO FORMULÁRIO (SUBMIT) ---
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const saveButton = document.getElementById('saveButton');
                saveButton.disabled = true;
                saveButton.innerText = 'Salvando...';

                // Validação de campos obrigatórios
                const nome = document.getElementById('nome').value;
                const telefone = document.getElementById('telefone').value;
                const cidade = document.getElementById('cidade').value;
                if (!nome || !telefone || !cidade) {
                    showStatus('Por favor, preencha os campos obrigatórios (Nome, Telefone e Cidade).', 'erro');
                    saveButton.disabled = false;
                    saveButton.innerText = 'Salvar Ficha';
                    return;
                }

                // Coletar dados do formulário
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    data[key] = value;
                });
                
                data.esteve_plantao = data.esteve_plantao === 'sim' ? 1 : 0;
                data.foi_atendido = data.foi_atendido === 'sim' ? 1 : 0;
                data.autoriza_transmissao = data.autoriza_transmissao === 'sim' ? 1 : 0;

                data.foto_cliente_base64 = fotoHiddenInput.value;
                data.assinatura_base64 = assinaturaHiddenInput.value;

                try {
                    const response = await fetch('/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();

                    if (result.success) {
                        showStatus('Ficha salva com sucesso!', 'sucesso');
                        form.reset();
                        clearSignatureBtn.click();
                        clearPhotoBtn.click();
                        toggleNomeCorretor(); // Resetar campo condicional
                    } else {
                        showStatus(`Erro ao salvar: ${result.message}`, 'erro');
                    }
                } catch (error) {
                    console.error('Erro no fetch:', error);
                    showStatus('Erro de conexão. Tente novamente.', 'erro');
                } finally {
                    saveButton.disabled = false;
                    saveButton.innerText = 'Salvar Ficha';
                }
            });

            function showStatus(message, type) {
                statusMessage.innerText = message;
                statusMessage.classList.remove('hidden');
                if (type === 'sucesso') {
                    statusMessage.classList.add('bg-green-200', 'text-green-800');
                    statusMessage.classList.remove('bg-red-200', 'text-red-800');
                } else {
                    statusMessage.classList.add('bg-red-200', 'text-red-800');
                    statusMessage.classList.remove('bg-green-200', 'text-green-800');
                }

                setTimeout(() => {
                    statusMessage.classList.add('hidden');
                }, 5000);
            }
        });
    </script>
</body>
</html>
"""

# --- Funções Auxiliares ---

def formatar_telefone_n8n(telefone_bruto):
    """
    Limpa e formata o número de telefone para o padrão E.164 para o n8n.
    Ex: (66) 99988-7766 -> +5566999887766
    """
    try:
        numeros = ''.join(filter(str.isdigit, telefone_bruto))
        if 10 <= len(numeros) <= 11:
            return f"+55{numeros}"
        else:
            print(f"Número de telefone inválido (comprimento): {telefone_bruto}")
            return None
    except Exception as e:
        print(f"Erro ao formatar telefone {telefone_bruto}: {e}")
        return None


# --- Rotas da Aplicação Flask ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Rota principal:
    - GET: Exibe o formulário HTML (passando a lista de empreendimentos).
    - POST: Recebe os dados, salva no BD e envia Webhook para o n8n.
    """
    if request.method == 'POST':
        
        if not DATABASE_URL:
            return jsonify({'success': False, 'message': 'Configuração do banco de dados não encontrada.'}), 500

        try:
            data = request.json
            
            # Dados principais
            nome = data.get('nome')
            telefone_bruto = data.get('telefone')
            cidade = data.get('cidade')
            
            # Campos novos
            loteamento = data.get('loteamento')
            comprou_1o_lote = data.get('comprou_1o_lote')
            nivel_interesse = data.get('nivel_interesse')
            
            # Formata o telefone para E.164
            telefone_formatado = formatar_telefone_n8n(telefone_bruto)
            
            # Validações
            if not telefone_formatado:
                return jsonify({'success': False, 'message': 'Número de telefone inválido.'}), 400
            
            if not nome or not cidade:
                return jsonify({'success': False, 'message': 'Nome e Cidade são obrigatórios.'}), 400

            # Restante dos dados
            rede_social = data.get('rede_social')
            abordagem_inicial = data.get('abordagem_inicial')
            esteve_plantao = data.get('esteve_plantao') == 1
            foi_atendido = data.get('foi_atendido') == 1
            nome_corretor_raw = data.get('nome_corretor')
            nome_corretor = nome_corretor_raw if foi_atendido and nome_corretor_raw else None
            autoriza_transmissao = data.get('autoriza_transmissao') == 1
            foto_cliente_base64 = data.get('foto_cliente_base64')
            assinatura_base64 = data.get('assinatura_base64')
            data_hora = datetime.datetime.now(datetime.timezone.utc)

            # 1. Inserir no banco de dados e RETORNAR O ID
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
            
            print(f"Ficha salva no BD. ID: {ticket_id}")

            # 2. Enviar para o n8n (Webhook Trigger)
            if N8N_WEBHOOK_URL:
                try:
                    payload_n8n = {
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
                    
                    response_n8n = requests.post(N8N_WEBHOOK_URL, json=payload_n8n, timeout=3)
                    print(f"Webhook n8n enviado. Status: {response_n8n.status_code}")
                    
                except Exception as e_n8n:
                    print(f"AVISO: Erro ao comunicar com n8n: {e_n8n}")
            
            return jsonify({'success': True, 'message': 'Ficha salva com sucesso!'})

        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            return jsonify({'success': False, 'message': f"Erro interno: {str(e)}"}), 500

    # Método GET: Renderiza o HTML injetando a lista de empreendimentos
    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS)


@app.route('/logo.jpg')
def serve_logo():
    """
    Decodifica a string Base64 do logo e serve como imagem JPEG.
    """
    try:
        image_data = base64.b64decode(LOGO_BASE64_STRING)
        return Response(image_data, mimetype='image/jpeg')
    except Exception as e:
        print(f"Erro ao servir logo: {e}")
        return "Erro no logo", 500


# --- Execução da Aplicação ---
if __name__ == '__main__':
    print("Iniciando banco de dados...")
    init_db()
    print(f"URL do n8n configurada: {N8N_WEBHOOK_URL}")
    print("Iniciando aplicação Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)
