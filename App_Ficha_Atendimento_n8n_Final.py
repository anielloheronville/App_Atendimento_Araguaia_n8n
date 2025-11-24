import flask
from flask import Flask, request, render_template_string, jsonify
import psycopg2
import os
import datetime
import requests

# --- Configuração da Aplicação ---
app = Flask(__name__)

# --- CONFIGURAÇÕES DE PRODUÇÃO (ENV VARS) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTA DE EMPREENDIMENTOS (Configuração Manual) ---
# Edite aqui para atualizar a lista suspensa no formulário
OPCOES_EMPREENDIMENTOS = [
    "Lançamento - Reserva do Bosque",
    "Lançamento - Altavista Premium",
    "Residencial Araguaia (Disponível)",
    "Jardim dos Ipês (> 10 Lotes)",
    "Vale do Sol (> 10 Lotes)",
    "Outros"
]

# --- TEMPLATE HTML (SEM LOGO) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha de Atendimento</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background-color: #f4f4f9; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            margin: 0; 
        }
        .container { 
            background-color: #ffffff; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
            width: 100%; 
            max-width: 600px; 
        }
        h2 { 
            text-align: center; 
            color: #333; 
            margin-bottom: 20px; 
            border-bottom: 2px solid #28a745;
            padding-bottom: 10px;
        }
        
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
        input[type="text"], input[type="email"], input[type="tel"], select, textarea {
            width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 14px;
        }
        input:focus, select:focus, textarea:focus { border-color: #007bff; outline: none; }
        
        button { 
            width: 100%; 
            padding: 12px; 
            background-color: #28a745; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            font-size: 16px; 
            cursor: pointer; 
            transition: background-color 0.3s; 
            margin-top: 10px;
        }
        button:hover { background-color: #218838; }
        
        .message { margin-top: 15px; padding: 10px; border-radius: 5px; text-align: center; display: none; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>

<div class="container">
    <h2>Ficha de Atendimento</h2>

    <form id="attendanceForm" method="POST">
        
        <div class="form-group">
            <label for="nome_cliente">Nome do Cliente:</label>
            <input type="text" id="nome_cliente" name="nome_cliente" required placeholder="Digite o nome completo">
        </div>

        <div class="form-group">
            <label for="telefone">Telefone / WhatsApp:</label>
            <input type="tel" id="telefone" name="telefone" required placeholder="(XX) XXXXX-XXXX">
        </div>

        <div class="form-group">
            <label for="empreendimento">Loteamento / Empreendimento:</label>
            <select id="empreendimento" name="empreendimento" required>
                <option value="" disabled selected>Selecione uma opção...</option>
                {% for opcao in empreendimentos %}
                    <option value="{{ opcao }}">{{ opcao }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-group">
            <label for="comprou_1o_lote">Realizou o sonho da compra do 1º Lote?</label>
            <select id="comprou_1o_lote" name="comprou_1o_lote" required>
                <option value="" disabled selected>Selecione...</option>
                <option value="Sim">Sim</option>
                <option value="Não">Não</option>
            </select>
        </div>

        <div class="form-group">
            <label for="interesse">Nível de Interesse:</label>
            <select id="interesse" name="interesse">
                <option value="Alto">Alto</option>
                <option value="Médio">Médio</option>
                <option value="Baixo">Baixo</option>
            </select>
        </div>

        <div class="form-group">
            <label for="observacoes">Observações:</label>
            <textarea id="observacoes" name="observacoes" rows="4" placeholder="Detalhes do atendimento..."></textarea>
        </div>

        <button type="submit" id="btnSubmit">Enviar Ficha</button>
    </form>

    <div id="responseMessage" class="message"></div>
</div>

<script>
    document.getElementById('attendanceForm').addEventListener('submit', function(e) {
        e.preventDefault();
        var btn = document.getElementById('btnSubmit');
        var msgDiv = document.getElementById('responseMessage');
        var formData = new FormData(this);

        btn.disabled = true;
        btn.innerText = 'Enviando...';
        msgDiv.style.display = 'none';

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            msgDiv.innerText = data.message;
            msgDiv.style.display = 'block';
            
            if(data.status === 'success') {
                msgDiv.className = 'message success';
                document.getElementById('attendanceForm').reset();
            } else {
                msgDiv.className = 'message error';
            }
        })
        .catch(error => {
            msgDiv.innerText = 'Erro ao conectar com o servidor.';
            msgDiv.className = 'message error';
            msgDiv.style.display = 'block';
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerText = 'Enviar Ficha';
        });
    });
</script>

</body>
</html>
"""

# --- ROTAS DA APLICAÇÃO ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # 1. Capturar dados do formulário
            data = {
                "data_hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nome_cliente": request.form.get("nome_cliente"),
                "telefone": request.form.get("telefone"),
                "empreendimento": request.form.get("empreendimento"),
                "comprou_1o_lote": request.form.get("comprou_1o_lote"), # Novo Campo
                "interesse": request.form.get("interesse"),
                "observacoes": request.form.get("observacoes")
            }

            # 2. Enviar para N8N (se URL configurada)
            if N8N_WEBHOOK_URL:
                try:
                    requests.post(N8N_WEBHOOK_URL, json=data, timeout=5)
                except Exception as e:
                    print(f"Erro ao enviar webhook N8N: {e}")
                    # Continua a execução para tentar salvar no banco

            # 3. Salvar no Banco de Dados (se URL configurada)
            if DATABASE_URL:
                try:
                    conn = psycopg2.connect(DATABASE_URL)
                    cur = conn.cursor()
                    
                    # Cria a tabela se não existir (incluindo o novo campo)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS atendimentos (
                            id SERIAL PRIMARY KEY,
                            data_hora TIMESTAMP,
                            nome_cliente TEXT,
                            telefone TEXT,
                            empreendimento TEXT,
                            comprou_1o_lote TEXT,
                            interesse TEXT,
                            observacoes TEXT
                        );
                    """)
                    
                    # Insere os dados
                    cur.execute("""
                        INSERT INTO atendimentos (data_hora, nome_cliente, telefone, empreendimento, comprou_1o_lote, interesse, observacoes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data['data_hora'], 
                        data['nome_cliente'], 
                        data['telefone'], 
                        data['empreendimento'], 
                        data['comprou_1o_lote'], 
                        data['interesse'], 
                        data['observacoes']
                    ))
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as db_err:
                    print(f"Erro banco de dados: {db_err}")
                    return jsonify({"status": "error", "message": "Erro ao salvar no banco de dados."}), 500

            return jsonify({"status": "success", "message": "Atendimento registrado com sucesso!"})

        except Exception as e:
            return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500

    # Se for GET, renderiza o formulário com a lista de opções
    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
