
import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]
API = "https://discord.com/api/v10"
STATE_FILE = "boss_state.json"

def discord_request(path, method="GET", data=None):
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(
        API + path, data=body, headers=headers, method=method
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()
        return json.loads(raw) if raw else {}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def parse_boss(content):
    boss = re.search(r"ชื่อบอส\s*[:：]\s*(.+)", content)
    hours = re.search(r"ชั่วโมงที่เหลือ\s*[:：]\s*(\d+)", content)
    minutes = re.search(r"นาทีที่เหลือ\s*[:：]\s*(\d+)", content)

    if not boss or not hours or not minutes:
        return None

    name = boss.group(1).strip()
    h = int(hours.group(1))
    m = int(minutes.group(1))

    if not name or h < 0 or not 0 <= m < 60:
        return None

    return name, h * 60 + m

def send_message(content):
    discord_request(
        f"/channels/{CHANNEL_ID}/messages",
        method="POST",
        data={"content": content}
    )

def main():
    state = load_state()

    messages = discord_request(
        f"/channels/{CHANNEL_ID}/messages?limit=100"
    )

    now = datetime.now(timezone.utc)

    for message in reversed(messages):
        if message.get("author", {}).get("bot"):
            continue

        parsed = parse_boss(message.get("content", ""))
        if not parsed:
            continue

        boss_name, remaining_minutes = parsed
        message_id = message["id"]

        created = datetime.fromisoformat(
            message["timestamp"].replace("Z", "+00:00")
        )

        spawn_time = created + timedelta(minutes=remaining_minutes)

        if message_id not in state:
            state[message_id] = {
                "boss": boss_name,
                "spawn": spawn_time.isoformat(),
                "sent": []
            }

        record = state[message_id]
        spawn_time = datetime.fromisoformat(record["spawn"])

        alerts = [
            (10, "อีก 10 นาที"),
            (5, "อีก 5 นาที"),
            (0, "เกิดแล้ว!")
        ]

        for minutes_before, label in alerts:
            alert_time = spawn_time - timedelta(minutes=minutes_before)
            key = str(minutes_before)

            if now >= alert_time and key not in record["sent"]:
                send_message(
                    f"🔔 **{record['boss']}** — {label}\n"
                    f"เซิร์ฟเวอร์ Spinel 2"
                )
                record["sent"].append(key)

    save_state(state)

if __name__ == "__main__":
    main()
