from flask import Flask, request, jsonify
from gpt4all import GPT4All
from flask_cors import CORS

app = Flask(__name__)

model = GPT4All("gpt4all-13b-snoozy-q4_0.gguf", device="cuda")

CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    response = model.generate(user_message)
    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
