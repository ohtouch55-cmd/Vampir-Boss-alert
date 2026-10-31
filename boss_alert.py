import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
CHANNEL_ID = os.environ["DISCORD_CHANNEL_ID"]
API = "https://discord.com/api/v10"
STATE_FILE = "boss_state.json"
THAI_TZ = timezone(timedelta(hours=7))

BOSSES = {
    "12:00": [
        "เดเซอร์ต LV83",
        "ยูเซอร์พาเตอร์ LV107",
        "บราคิอุม LV63"
    ],
    "20:00": [
        "เคลมามุส LV70",
        "เอ็กเซซา LV95",
        "ลาร์บา LV47"
    ]
}

def discord_send(message):
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/channels/{CHANNEL_ID}/messages",
        data=data,
        headers={
            "Authorization": f"Bot {TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        response.read()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sent": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    now = datetime.now(THAI_TZ)
    today = now.strftime("%Y-%m-%d")
    current = now.hour * 60 + now.minute

    state = load_state()
    sent = set(state.get("sent", []))

    alerts = [
        (10, "อีก 10 นาที"),
        (5, "อีก 5 นาที"),
        (0, "เกิดแล้ว!")
    ]

    for spawn, bosses in BOSSES.items():
        hour, minute = map(int, spawn.split(":"))
        spawn_minutes = hour * 60 + minute

        for lead, label in alerts:
            alert_minutes = spawn_minutes - lead
            key = f"{today}_{spawn}_{lead}"

            if alert_minutes <= current < alert_minutes + 5:
                if key not in sent:
                    names = "\n".join(f"• {boss}" for boss in bosses)
                    message = (
                        f"⚔️ **VAMPIR BOSS ALERT**\n"
                        f"เซิร์ฟเวอร์: **Spinel 2**\n"
                        f"บอส: **{label}**\n"
                        f"{names}\n"
                        f"เวลาเกิด: **{spawn} น.** (เวลาไทย)"
                    )
                    discord_send(message)
                    sent.add(key)

    state["sent"] = sorted(sent)
    save_state(state)

if __name__ == "__main__":
    main()
