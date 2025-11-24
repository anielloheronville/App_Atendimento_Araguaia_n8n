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
    "Lançamento - Reserva do Bosque",
    "Lançamento - Altavista Premium",
    "Residencial Araguaia (Disponível)",
    "Jardim dos Ipês (> 10 Lotes)",
    "Vale do Sol (> 10 Lotes)",
    "Outros"
]

# --- BANCO DE DADOS (COM MIGRAÇÃO AUTOMÁTICA) ---
def init_db():
    """
    Verifica a tabela e cria as colunas novas se elas não existirem.
    Isso corrige o erro 'column does not exist'.
    """
    if not DATABASE_URL:
        logger.warning("⚠️ AVISO: DATABASE_URL não encontrada. O app não salvará dados.")
        return

    # 1. Query da Tabela Base
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

    # 2. Queries de Migração (Adicionar colunas novas)
    migrations = [
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;"
    ]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()

        # Cria a tabela se não existir
        cursor.execute(create_table_query)
        
        # Tenta aplicar as migrações (ignora erro se já existirem)
        for migration in migrations:
            try:
                cursor.execute(migration)
                logger.info(f"Migração aplicada: {migration}")
            except Exception as e_mig:
                logger.info(f"Nota de migração (coluna provavelmnete já existe): {e_mig}")

        cursor.close()
        conn.close()
        logger.info("✅ Banco de dados atualizado e pronto.")

    except Exception as e:
        logger.error(f"❌ Erro crítico ao inicializar Banco de Dados: {e}")

# --- INICIALIZA O BANCO AO RODAR O SCRIPT ---
init_db()

# --- TEMPLATE HTML (SEM LOGO) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha de Pré Atendimento - Araguaia Imóveis</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
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
        .btn-salvar {
            background-color: var(--cor-botao-verde);
            color: #2d333b;
            font-weight: bold;
            padding: 0.75rem 1.5rem;
            border-radius: 0.375rem;
            transition: all 0.2s;
            cursor: pointer;
        }
        .btn-salvar:hover { opacity: 0.85; }
        .btn-salvar:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .signature-canvas, .photo-canvas, .video-preview {
            border: 1px dashed var(--cor-borda);
            border-radius: 0.375rem;
            background-color: #5a616c;
        }
        .hidden { display: none; }
        .btn-limpar {
            color: var(--cor-texto-medio);
            font-size: 0.875rem;
            text-decoration: underline;
            cursor: pointer;
        }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <nav class="w-full bg-transparent p-4 md:p-6">
        <div class="container mx-auto flex justify-center items-center max-w-6xl">
            <span class="text-lg md:text-xl font-bold tracking-widest" style="color: var(--cor-botao-verde);">
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
                            <span class="block text-sm font-medium mb-2">Já esteve em um dos plantões?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="esteve_plantao" value="sim" required> <span class="ml-2">Sim</span></label>
                                <label><input type="radio" name="esteve_plantao" value="nao"> <span class="ml-2">Não</span></label>
                            </div>
                        </div>

                        <div>
                            <span class="block text-sm font-medium mb-2">Já foi atendido por corretor?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="foi_atendido" value="sim" id="atendido_sim" required> <span class="ml-2">Sim</span></label>
                                <label><input type="radio" name="foi_atendido" value="nao" id="atendido_nao"> <span class="ml-2">Não</span></label>
                            </div>
                        </div>
                        
                        <div id="campoNomeCorretor" class="hidden">
                            <label for="nome_corretor" class="block text-sm font-medium mb-2">Se sim, qual o nome:</label>
                            <input type="text" id="nome_corretor" name="nome_corretor" class="form-input">
                        </div>

                        <div>
                            <span class="block text-sm font-medium mb-2">Autoriza lista de transmissão?*</span>
                            <div class="flex gap-4">
                                <label><input type="radio" name="autoriza_transmissao" value="sim" required> <span class="ml-2">Sim</span></label>
                                <label><input type="radio" name="autoriza_transmissao" value="nao"> <span class="ml-2">Não</span></label>
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
                    <span class="text-sm text-gray-300" id="dataAtual">Sorriso/MT</span>
                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto">Salvar Ficha</button>
                </div>

                <div id="statusMessage" class="md:col-span-2 text-center p-2 rounded hidden"></div>
            </form>
        </div>
    </main>

    <footer class="w-full p-4 mt-8 text-center text-xs text-gray-400">
        © <span id="currentYear"></span> Araguaia Imóveis.
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            
            // Atualiza data
            const today = new Date();
            document.getElementById('dataAtual').innerText = `Sorriso/MT, ${today.toLocaleDateString('pt-BR')}`;
            document.getElementById('currentYear').innerText = today.getFullYear();

            // Elementos
            const form = document.getElementById('preAtendimentoForm');
            const statusMessage = document.getElementById('statusMessage');
            
            // Câmera
            const video = document.getElementById('videoPreview');
            const photoCanvas = document.getElementById('photoCanvas');
            const photoCtx = photoCanvas.getContext('2d');
            const startWebcamBtn = document.getElementById('startWebcam');
            const takePhotoBtn = document.getElementById('takePhoto');
            const clearPhotoBtn = document.getElementById('clearPhoto');
            const fotoHiddenInput = document.getElementById('foto_cliente_base64');
            let stream = null;

            function drawPlaceholder() {
                photoCtx.fillStyle = '#b0b0b0';
                photoCtx.fillRect(0, 0, photoCanvas.width, photoCanvas.height);
            }
            drawPlaceholder();

            startWebcamBtn.addEventListener('click', async () => {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = stream;
                    video.classList.remove('hidden');
                    photoCanvas.classList.add('hidden');
                    takePhotoBtn.classList.remove('hidden');
                    clearPhotoBtn.classList.remove('hidden');
                    startWebcamBtn.classList.add('hidden');
                } catch (err) {
                    alert("Erro ao acessar câmera (Permissão negada ou HTTPS ausente).");
                }
            });

            takePhotoBtn.addEventListener('click', () => {
                photoCanvas.width = video.videoWidth;
                photoCanvas.height = video.videoHeight;
                photoCtx.drawImage(video, 0, 0);
                fotoHiddenInput.value = photoCanvas.toDataURL('image/jpeg', 0.8);
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                if(stream) stream.getTracks().forEach(t => t.stop());
            });

            clearPhotoBtn.addEventListener('click', () => {
                drawPlaceholder();
                fotoHiddenInput.value = '';
                video.classList.add('hidden');
                photoCanvas.classList.remove('hidden');
                startWebcamBtn.classList.remove('hidden');
                takePhotoBtn.classList.add('hidden');
                clearPhotoBtn.classList.add('hidden');
                if(stream) stream.getTracks().forEach(t => t.stop());
            });

            // Campo Corretor Condicional
            const atendidoSim = document.getElementById('atendido_sim');
            const atendidoNao = document.getElementById('atendido_nao');
            const campoNome = document.getElementById('campoNomeCorretor');
            
            function toggleCorretor() {
                if(atendidoSim.checked) {
                    campoNome.classList.remove('hidden');
                    document.getElementById('nome_corretor').required = true;
                } else {
                    campoNome.classList.add('hidden');
                    document.getElementById('nome_corretor').required = false;
                }
            }
            atendidoSim.addEventListener('change', toggleCorretor);
            atendidoNao.addEventListener('change', toggleCorretor);

            // Assinatura
            const sigCanvas = document.getElementById('signatureCanvas');
            const sigCtx = sigCanvas.getContext('2d');
            let drawing = false;

            function resizeCanvas() {
                const rect = sigCanvas.getBoundingClientRect();
                sigCanvas.width = rect.width;
                sigCanvas.height = rect.height;
                sigCtx.strokeStyle = "#FFFFFF";
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

            // Envio do Formulário
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('saveButton');
                btn.disabled = true;
                btn.innerText = 'Salvando...';

                // Captura dados
                const formData = new FormData(form);
                const data = {};
                formData.forEach((val, key) => data[key] = val);

                // Tratamento de Booleans
                data.esteve_plantao = (data.esteve_plantao === 'sim') ? 1 : 0;
                data.foi_atendido = (data.foi_atendido === 'sim') ? 1 : 0;
                data.autoriza_transmissao = (data.autoriza_transmissao === 'sim') ? 1 : 0;
                
                // Dados binários
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
                        statusMessage.innerText = "Salvo com sucesso!";
                        statusMessage.className = "md:col-span-2 text-center p-2 rounded bg-green-200 text-green-800";
                        statusMessage.classList.remove('hidden');
                        form.reset();
                        sigCtx.clearRect(0,0,sigCanvas.width, sigCanvas.height);
                        drawPlaceholder();
                        toggleCorretor();
                    } else {
                        throw new Error(res.message);
                    }
                } catch (err) {
                    statusMessage.innerText = "Erro: " + err.message;
                    statusMessage.className = "md:col-span-2 text-center p-2 rounded bg-red-200 text-red-800";
                    statusMessage.classList.remove('hidden');
                } finally {
                    btn.disabled = false;
                    btn.innerText = 'Salvar Ficha';
                }
            });
        });
    </script>
</body>
</html>
"""

# --- Funções Auxiliares ---

def formatar_telefone_n8n(telefone_bruto):
    try:
        numeros = ''.join(filter(str.isdigit, telefone_bruto))
        if 10 <= len(numeros) <= 11:
            return f"+55{numeros}"
        return None
    except:
        return None

# --- ROTAS DA APLICAÇÃO ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not DATABASE_URL:
            return jsonify({'success': False, 'message': 'Banco de dados não configurado.'}), 500

        try:
            data = request.json
            
            # Campos Obrigatórios
            nome = data.get('nome')
            cidade = data.get('cidade')
            telefone_formatado = formatar_telefone_n8n(data.get('telefone'))
            
            if not telefone_formatado:
                return jsonify({'success': False, 'message': 'Telefone inválido.'}), 400
            if not nome or not cidade:
                return jsonify({'success': False, 'message': 'Nome e Cidade são obrigatórios.'}), 400

            # Campos Extras
            loteamento = data.get('loteamento')
            comprou_1o_lote = data.get('comprou_1o_lote')
            nivel_interesse = data.get('nivel_interesse')
            
            # Dados Gerais
            rede_social = data.get('rede_social')
            abordagem_inicial = data.get('abordagem_inicial')
            esteve_plantao = data.get('esteve_plantao') == 1
            foi_atendido = data.get('foi_atendido') == 1
            nome_corretor = data.get('nome_corretor') if foi_atendido else None
            autoriza_transmissao = data.get('autoriza_transmissao') == 1
            foto_cliente_base64 = data.get('foto_cliente_base64')
            assinatura_base64 = data.get('assinatura_base64')
            data_hora = datetime.datetime.now(datetime.timezone.utc)

            # 1. Salvar no Banco
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
            
            logger.info(f"Registro salvo ID: {ticket_id}")

            # 2. Enviar Webhook N8N
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
                    logger.warning(f"Falha webhook n8n: {e_n8n}")
            
            return jsonify({'success': True, 'message': 'Ficha salva com sucesso!'})

        except Exception as e:
            logger.error(f"Erro POST: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    # GET: Renderiza Template com as opções
    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS)

if __name__ == '__main__':
    # init_db já foi chamado no escopo global para garantir a migração no deploy
    app.run(host='0.0.0.0', port=5000, debug=True)
