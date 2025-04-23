from flask import Flask, request, jsonify, session
from gpt4all import GPT4All
from flask_cors import CORS
from flask_session import Session
import sqlite3

def init_db():
    conn = sqlite3.connect("chat_logs.db")
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

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'choris-secret'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

model = GPT4All("gpt4all-13b-snoozy-q4_0.gguf", device="cuda")

def save_log(user_message, bot_reply):
    conn = sqlite3.connect("chat_logs.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_message, bot_reply) VALUES (?, ?)",
        (user_message, bot_reply)
    )
    conn.commit()
    conn.close()

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect("chat_logs.db")
    cursor = conn.cursor() 
    cursor.execute("SELECT user_message, bot_reply, timestamp FROM chat_logs ORDER BY timestamp DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append({'user': row[0], 'bot': row[1], 'timestamp': row[2]})

    return jsonify({'logs': logs})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    if 'history' not in session:
        session['history'] = []

    session['history'].append({'role': 'user', 'content': user_message})

    formatted_history = ""
    for item in session['history']:
        role = "Usuário" if item['role'] == 'user' else "Chorão"
        formatted_history += f"{role}: {item['content']}\n"

    prompt = f"""
        Você é o Chorão BOT, assistente oficial do Choris Skatepark.
        Fale apenas em português, com respostas curtas, diretas e úteis.
        Você responde dúvidas sobre:
        - aluguel de pistas
        - valores
        - horários
        - manutenção de skates
        - equipamentos obrigatórios
        - segurança
        - modalidades (street, bowl, vertical)

        Evite repetir o que o usuário disse. Não fale sobre IA ou sobre você.
        Nunca use frases como "obrigado por me contatar".

        Histórico da conversa:
        {formatted_history}
        Chorão:
    """

    response = model.generate(prompt, max_tokens=200, temp=0.6)
    bot_reply = response.strip()

    session['history'].append({'role': 'bot', 'content': bot_reply})
    save_log(user_message, bot_reply)

    return jsonify({'reply': bot_reply})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
