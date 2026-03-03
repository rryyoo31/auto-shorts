import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

prompt = """
1万円だけ打つ男のショート動画台本を作れ。

条件：
・7セリフ構成
・セリフは短く鋭く
・断定スタート
・初心者向け
・冷静で思考を促すトーン
・最後は毎回少し表現を変えながらフォローを自然に促す
・30秒以内
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

script = response.choices[0].message.content

print("===== GENERATED SCRIPT =====")
print(script)
