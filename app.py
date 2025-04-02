from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    print("受信したWix注文データ:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
