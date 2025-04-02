from flask import Flask, request, send_from_directory
from docxtpl import DocxTemplate
import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

app = Flask(__name__)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    print("受信したWix注文データ:")
    print(data)

    # 注文タイトルからツアー名と日付を抽出（例：「2025/7/17～7/19 綠牌海獅包車3天」）
    title = data.get('planName') or data.get('title') or ''
    match = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})～(\d{1,2})/(\d{1,2})\s+(.+)", title)
    if not match:
        return "タイトル形式が不正です", 400

    year, start_month, start_day, end_month, end_day, tour_name = match.groups()
    start_date = f"{year}-{int(start_month):02d}-{int(start_day):02d}"

    # URLを生成（例：https://www.monchan-travel.com/en/service-page/YYYY-MM-DD-ツアー名）
    tour_slug = f"{start_date}-{tour_name}".replace(" ", "-")
    tour_slug = re.sub(r"[^\w\-一-龥]", "", tour_slug)  # 記号削除
    url = f"https://www.monchan-travel.com/en/service-page/{tour_slug}"
    print("推定ツアーURL:", url)

    # ツアーページからHTMLを取得して解析
    try:
        res = requests.get(url)
        res.raise_for_status()
    except Exception as e:
        return f"ツアーページ取得エラー: {e}", 500

    soup = BeautifulSoup(res.text, "html.parser")
    tour_text = soup.get_text(separator="\n", strip=True)

    # シンプルな例として「集合場所」や「日程」のキーワードを抽出
    context = {
        "group_name": data.get("customer", {}).get("firstName", "") + " 様",
        "arrival": f"{start_month}/{start_day}",
        "departure": f"{end_month}/{end_day}",
        "meeting_place": "（例）新千歳空港",  # 固定でもよければここに
        "schedule": tour_text[:300] + "..."  # 仮で先頭300文字を差し込み
    }

    # Wordファイル生成（行程表と手配書）
    generate_doc("行程表テンプレート.docx", f"行程表_{start_date}.docx", context)
    generate_doc("手配書テンプレート.docx", f"手配書_{start_date}.docx", context)

    return {"message": "行程表と手配書を生成しました", "download": f"/download/行程表_{start_date}.docx"}, 200

def generate_doc(template_name, output_name, context):
    template_path = os.path.join(template_name)
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(os.path.join(OUTPUT_DIR, output_name))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
