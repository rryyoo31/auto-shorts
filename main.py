import os
import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# JSTの曜日で判定
jst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
weekday = jst_now.strftime("%a")  # Mon Tue Wed Thu Fri Sat Sun

if weekday in ["Mon", "Tue", "Thu", "Fri"]:
    theme = "初心者がやるな系（断定・撤退・基準）"
elif weekday in ["Wed", "Sat"]:
    theme = "数字・おすすめ系（確率/回転率/持ち玉比率/機種例）"
else:
    theme = "焼き直し・強ワード系（初心者の地雷を言い切る）"

prompt = f"""
今日のテーマ：{theme}

以下のJSON形式のみで出力せよ。

{{
"title": "",
"lines": ["①", "②", "③", "④", "⑤", "⑥", "⑦"],
"follow": "",
"next": "",
"description": "",
"comment": ""
}}

絶対にJSON以外の文章を書くな。
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    response_format={"type": "json_object"}
)

script = response.choices[0].message.content

print("===== GENERATED SCRIPT =====")
print(script)
