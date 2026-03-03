import os
import json
import random
from openai import OpenAI
from datetime import datetime

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# =========================
# テーマランダム化
# =========================

themes = [
    "初心者がやるな系",
    "1万円勝負の基準",
    "撤退ライン",
    "勝ちを守る思考",
    "負けパターン分析",
    "回転率の見方",
    "感情で打つな",
]

theme = random.choice(themes)

# =========================
# プロンプト
# =========================

prompt = f"""
テーマ：{theme}

以下のJSON形式のみで出力せよ。

{{
"title": "",
"lines": ["①", "②", "③", "④", "⑤", "⑥", "⑦"],
"follow": "",
"next": "",
"description": "",
"comment": ""
}}

条件：
・断定スタート
・初心者向け
・冷静トーン
・フォロー自然誘導
・30秒以内
・JSON以外絶対に出力するな
"""

# =========================
# GPT実行
# =========================

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
)

content = response.choices[0].message.content

data = json.loads(content)

# =========================
# 保存
# =========================

today = datetime.now().strftime("%Y-%m-%d")

os.makedirs("output", exist_ok=True)

with open(f"output/{today}.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("===== GENERATED SCRIPT =====")
print(json.dumps(data, ensure_ascii=False, indent=2))
