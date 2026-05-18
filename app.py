import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. 讀取 .env 檔案
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允許你的 index.html 跨網域呼叫

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

if __name__ == '__main__':
    # 讓伺服器跑在 port 3000
    app.run(port=3000, debug=True)