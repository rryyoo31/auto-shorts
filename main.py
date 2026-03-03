import os
import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# 今日の曜日を取得
weekday = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekday = weekday.strftime("%a")

# 曜日ごとにテーマ分岐
if weekday in ["Mon", "Tue", "Thu", "Fri"]:
    theme = "初心者がやるな系"
elif weekday in ["Wed", "Sat"]:
    theme = "数字・おすすめ系"
else:
    theme = "焼き直し・強ワード系"

prompt = f"""
1万円だけ打つ男のショート動画台本を作れ。

今日のテーマ：{theme}

出力フォーマットは必ず守れ：

タイトル：
①
②
③
④
⑤
⑥
⑦
（固定別枠）
次▶︎
説明文＋ハッシュタグ：
固定コメント：

条件：
・7セリフ構成
・断定スタート
・冷静トーン
・初心者向け
・最後は少し変化をつけながらフォローを促す
・30秒以内
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)

script = response.choices[0].message.content

print("===== GENERATED SCRIPT =====")
print(script)
