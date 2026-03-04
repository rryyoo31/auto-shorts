import os
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from openai import OpenAI

DAYS = ["月", "火", "水", "木", "金", "土", "日"]

STATE_FILE = "state.json"
HISTORY_FILE = "history.json"
OUT_DIR = "generated"
MAX_TRIES = 5  # 70点未満 or 被りなら再生成


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def normalize_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("：", ":")
    return s


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def overlap_score(candidate: dict, history: list[dict]) -> float:
    """過去20本と、タイトル・セリフの近さ最大値を返す"""
    if not history:
        return 0.0
    last = history[-20:]
    cand_blob = "\n".join([candidate.get("title", "")] + candidate.get("lines", []))
    best = 0.0
    for h in last:
        h_blob = "\n".join([h.get("title", "")] + h.get("lines", []))
        best = max(best, similarity(cand_blob, h_blob))
    return best


def format_output(day: str, slot: int, video_number: int, data: dict) -> str:
    lines = data["lines"]
    out = []
    out.append(f"({day}{'①' if slot == 1 else '②'}){video_number}本目")
    out.append(data["title"])
    out.append("")
    for i, s in enumerate(lines, start=1):
        out.append(f"セリフ{i}：{s}")
    out.append("")
    out.append("固定別枠：基準で打つならフォロー。")
    out.append(f"次▶︎{data['next']}")
    out.append("")
    out.append(f"説明文＋ハッシュタグ：{data['description']}")
    out.append(f"固定コメント：{data['comment']}")
    return "\n".join(out)

def compute_next_state(state: dict) -> dict:
    day_index = int(state["day_index"])
    slot = int(state["slot"])
    video_number = int(state["video_number"])

    video_number += 1

    if slot == 1:
        slot = 2
    else:
        slot = 1
        day_index = (day_index + 1) % 7

    return {"day_index": day_index, "slot": slot, "video_number": video_number}


def build_prompt(day: str, slot: int, video_number: int, prev_next_title: str | None) -> str:
    rule_next = (
        "今回のタイトルは、前回の次回予告タイトルと完全一致させる。"
        if prev_next_title
        else "今回のタイトルは短く強く断定。"
    )

    fixed_title = f"【今回タイトル固定】{prev_next_title}" if prev_next_title else ""

    return (
        "あなたはYouTube Shorts台本の生成AI。\n"
        "チャンネル：1万円だけ打つ男\n\n"
        "絶対ルール：\n"
        "1) タイトルとセリフ①は完全一致\n"
        "2) セリフは①〜⑦の7つ。短め。\n"
        "3) 断定スタート。初心者向け。煽りすぎない。\n"
        "4) 固定別枠は必ず『基準で打つならフォロー。』\n"
        "5) 次回予告は『次▶︎（タイトル）』形式で出す\n"
        "6) 説明文とハッシュタグは同じ枠（分けない）\n"
        "7) 出力はJSONのみ（余計な文章禁止）\n"
        f"8) {rule_next}\n\n"
        f"今日の枠：({day}{'①' if slot==1 else '②'}){video_number}本目\n"
        f"{fixed_title}\n\n"
        "JSONスキーマ：\n"
        "{\n"
        '  "title": "string",\n'
        '  "lines": ["セリフ①","セリフ②","セリフ③","セリフ④","セリフ⑤","セリフ⑥","セリフ⑦"],\n'
        '  "next": "次回予告タイトル（次▶︎は付けない）",\n'
        '  "description": "説明文＋ハッシュタグ（同一枠）",\n'
        '  "comment": "固定コメント"\n'
        "}\n\n"
        "追加条件：\n"
        "- title と lines[0] を完全一致\n"
        "- linesは7個ちょうど\n"
        "- next は次回のタイトルになるので短く強く\n"
        "- description は短め＋ハッシュタグ5〜8個\n"
        "- comment は一言。質問誘導も可\n"
    )


def parse_json_strict(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)

    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("title invalid")
    if not isinstance(data.get("lines"), list) or len(data["lines"]) != 7:
        raise ValueError("lines must be length 7")
    if normalize_text(data["title"]) != normalize_text(data["lines"][0]):
        raise ValueError("title and line1 must match exactly")
    for k in ["next", "description", "comment"]:
        if not isinstance(data.get(k), str):
            raise ValueError(f"{k} invalid")
    return data


def score_candidate(data: dict, history: list[dict]) -> int:
    score = 100

    ov = overlap_score(data, history)
    if ov >= 0.90:
        score -= 60
    elif ov >= 0.86:
        score -= 40
    elif ov >= 0.82:
        score -= 25

    avg_len = sum(len(s) for s in data["lines"]) / 7
    if avg_len > 32:
        score -= 15
    if avg_len > 40:
        score -= 20

    weak = ["かも", "と思う", "〜です", "〜ます"]
    head = data["lines"][0]
    if any(w in head for w in weak):
        score -= 15

    if not data["next"].strip():
        score -= 30
    if len(data["next"]) > 24:
        score -= 10

    return max(score, 0)


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    client = OpenAI(api_key=api_key)

    state = load_json(STATE_FILE, None)
    if state is None:
        raise RuntimeError("state.json がない")

    history = load_json(HISTORY_FILE, [])

    day = DAYS[int(state["day_index"])]
    slot = int(state["slot"])
    video_number = int(state["video_number"])

    prev_next = history[-1]["next"] if history else None

    best = None
    best_score = -1
    last_error = None

    for _ in range(MAX_TRIES):
        prompt = build_prompt(day, slot, video_number, prev_next)

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "出力はJSONのみ。余計な文章は禁止。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )

        text = res.choices[0].message.content
        try:
            data = parse_json_strict(text)
            s = score_candidate(data, history)
            if s > best_score:
                best, best_score = data, s
            if s >= 70:
                break
        except Exception as e:
            last_error = str(e)
            continue

    if best is None:
        raise RuntimeError(f"生成失敗: {last_error}")

    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_txt = format_output(day, slot, video_number, best)

    txt_path = os.path.join(OUT_DIR, f"{stamp}_v{video_number}.txt")
    json_path = os.path.join(OUT_DIR, f"{stamp}_v{video_number}.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(out_txt)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)

    history.append(best)
    save_json(HISTORY_FILE, history)

    next_state = compute_next_state(state)
    save_json(STATE_FILE, next_state)

    print("===== GENERATED SCRIPT =====")
    print(out_txt)
    print("")
    print(f"[score] {best_score}/100")
    print(f"[saved] {txt_path}")
    print(f"[saved] {json_path}")
    print(f"[next_state] {next_state}")


if __name__ == "__main__":
    main()
