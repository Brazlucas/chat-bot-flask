from flask import Flask, request, jsonify, session
from gpt4all import GPT4All
from flask_cors import CORS
from flask_session import Session
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat_logs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_log(user_message, bot_reply):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (user_message, bot_reply) VALUES (?, ?)", (user_message, bot_reply))
    conn.commit()
    conn.close()

def clear_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_logs")
    conn.commit()
    conn.close()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'choris-secret'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf", device="cuda")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    if 'history' not in session:
        session['history'] = []

    session['history'].append({'role': 'user', 'content': user_message})

    formatted_history = ""
    for item in session['history']:
        formatted_history += item['content'] + "\n"

    prompt = f"""
Você é o **Chorão BOT**, o mano das pistas, assistente do *Choris Skatepark*.

Fala igual um skatista das ruas — estilo maloqueiro, direto e firmeza. 
Responde dúvidas sobre:
Aluguel de pistas (quanto custa, quanto tempo dá pra ficar, se tá liberado ou não)
Horários e reservas
Modalidades de skate (street, bowl, vertical)
Dicas pra quem tá começando ou já tá na brisa faz tempo
Regras do parque, segurança e manutenção

Atenção:
Só fala em **português** e na moral do rolê
Nada de papo furado tipo “obrigado por me chamar”
Não repete o que o mano falou
Esquece esse lance de inteligência artificial, tu é o Chorão, firmeza?
Só troca ideia sobre o universo do skate. Fora disso, ignora
Preço dos horários, apenas estes:
100 reais por uma hora
200 reais por duas horas
500 reais para o dia todo

Manda no estilo: objetivo, sagaz e com aquele jeitão de quem vive a parada.

{formatted_history}
"""

    response = model.generate(prompt, max_tokens=200, temp=0.6)
    bot_reply = response.strip()

    session['history'].append({'role': 'bot', 'content': bot_reply})
    save_log(user_message, bot_reply)

    return jsonify({'reply': bot_reply})

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, bot_reply, timestamp FROM chat_logs ORDER BY id DESC")
    logs = [{'user': row[0], 'bot': row[1], 'timestamp': row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({'logs': logs})

@app.route('/reset', methods=['POST'])
def reset_session():
    session.pop('history', None)
    clear_logs()
    return jsonify({'message': 'Sessão e logs resetados com sucesso!'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
