import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pyrebase

# 1. 讀取 .env 檔案
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允許你的 index.html 跨網域呼叫

# ==========================================
# 🔒 1. 初始化 Google Gemini AI (最新版 SDK)
# ==========================================
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 🔒 2. 在後端安全初始化 Firebase 連線
# ==========================================
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# 2. 初始化 Gemini 客戶端
client = genai.Client()

@app.route('/api/recipe', methods=['POST'])
def get_recipe():
    try:
        # 接收前端食材
        data = request.json
        user_ingredients = data.get('ingredients', '')
        
        if not user_ingredients:
            return jsonify({"error": "請提供食材內容"}), 400

        # 設定 ESG 惜食主廚提示詞
        system_instruction = """
        你是一位精通零浪費料理的「ESG 惜食主廚」。
        你的任務是根據用戶提供的剩餘食材，設計出一份創意、美味且能完美消耗剩食的食譜。
        
        請遵循以下規則：
        1. 只能使用用戶提及的食材作為主料，可以假設用戶家中有常見調味料、油、鹽、糖、醬油、水等基礎備料。
        2. 如果食材組合很怪異，請發揮創意轉化為合理的料理。
        3. 回覆格式必須包含：
           - 🍳 【料理名稱】
           - 🌱 【ESG 減碳悄悄話】（一兩句話即可）
           - 🛒 【所需食材】
           - 📝 【料理步驟】
        """
        
        # 呼叫 Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"我手邊剩餘的食材有：{user_ingredients}。請幫我設計一份惜食食譜！",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        
        return jsonify({"recipe": response.text})

    except Exception as e:
        print(f"後端發生錯誤: {e}")
        return jsonify({"error": "AI 產生食譜時發生錯誤"}), 500

# 🟢 功能二：惜食小學堂 (幫前端安全撈取 Firebase 題目)
@app.route('/api/quiz', methods=['GET'])
def get_quiz_data():
    try:
        quiz_snapshot = db.child("quizData").get()
        raw_data = quiz_snapshot.val()
        
        if raw_data:
            if isinstance(raw_data, dict):
                temp_list = [value for value in raw_data.values()]
            else:
                temp_list = [x for x in raw_data if x is not None]
            return jsonify(temp_list)
        else:
            return jsonify({"error": "Firebase 中找不到 quizData 節點"}), 404
    except Exception as e:
        print(f"後端讀取題目發生錯誤: {e}")
        return jsonify({"error": str(e)}), 500


# 🟢 功能三：雲端連署 (安全讀取目前的連署總人數)
@app.route('/api/pledge/count', methods=['GET'])
def get_pledge_count():
    try:
        # 對齊妳資料庫原先的節點名稱：pledge_total
        count = db.child("pledge_total").get().val()
        if count is None:
            count = 0
        return jsonify({"count": count})
    except Exception as e:
        print(f"獲取連署人數失敗: {e}")
        return jsonify({"error": str(e)}), 500


# 🟢 功能四：雲端連署 (安全地讓資料庫人數 + 1)
@app.route('/api/pledge/increment', methods=['POST'])
def increment_pledge():
    try:
        current_count = db.child("pledge_total").get().val()
        if current_count is None:
            current_count = 0
            
        new_count = current_count + 1
        db.child("pledge_total").set(new_count)
        return jsonify({"success": True, "count": new_count})
    except Exception as e:
        print(f"連署增加失敗: {e}")
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)