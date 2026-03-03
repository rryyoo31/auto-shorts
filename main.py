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
あなたは「1万円だけ打つ男」。
YouTube Shorts向けの台本を1本作る。

【今日のテーマ】
{theme}

【絶対ルール（破ったら失格）】
- 出力は“指定フォーマット”の行だけ。余計な説明禁止
- タイトル＝セリフ①と完全一致（句読点も一致）
- セリフは①〜⑦を必ず使う（各1行、短く）
- 断定スタート、冷静、初心者向け
- 「基準で打つならフォロー。」は使わない（毎回違う言い方でフォロー誘導）
- 次回予告は「次▶︎（タイトル）」の形で必ず出す
- 説明文＋ハッシュタグは1つの塊で出す（分けない）
- 固定コメントも必ず出す
- 全体で30秒想定（無駄に長くしない）

【指定フォーマット（1文字も崩すな）】
タイトル：
①
②
③
④
⑤
⑥
⑦
固定別枠：
次▶︎（タイトル）
説明文＋ハッシュタグ：
固定コメント：
出力はプレーンテキストのみ。
番号は必ず①②③④⑤⑥⑦を使用。
半角数字禁止。
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.4
)

script = response.choices[0].message.content

print("===== GENERATED SCRIPT =====")
print(script)
