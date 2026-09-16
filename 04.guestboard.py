import hashlib
import html
import json
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

DATA_FILE = "guestboard.json"
KST = ZoneInfo("Asia/Seoul")


def load_entries() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_entries(entries: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


AVATAR_COLORS = ["#2563eb", "#0ea5e9", "#6366f1", "#0891b2", "#3b82f6", "#4f46e5"]


def avatar_color(name: str) -> str:
    return AVATAR_COLORS[sum(ord(c) for c in name) % len(AVATAR_COLORS)]


def render_entry(entry: dict) -> str:
    name = html.escape(entry["name"])
    message = html.escape(entry["message"]).replace("\n", "<br>")
    created = entry["created_at"]
    initial = html.escape(entry["name"][:1].upper())
    color = avatar_color(entry["name"])

    return f"""
    <li class="entry">
        <div class="entry-head">
            <div class="avatar" style="background:{color}">{initial}</div>
            <div class="entry-meta">
                <span class="entry-name">{name}</span>
                <span class="entry-date">{created}</span>
            </div>
            <details class="delete-toggle">
                <summary>삭제</summary>
                <form method="post" action="/entries/{entry['id']}/delete" class="delete-form">
                    <input type="password" name="password" placeholder="비밀번호" required>
                    <button type="submit">확인</button>
                </form>
            </details>
        </div>
        <p class="entry-message">{message}</p>
    </li>
    """


def render_page(entries: list[dict], error: str | None = None) -> str:
    if entries:
        items = "\n".join(render_entry(e) for e in reversed(entries))
        list_html = f'<ul class="entry-list">{items}</ul>'
    else:
        list_html = '<p class="empty">아직 방명록이 없어요. 첫 글을 남겨보세요!</p>'

    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>방명록</title>
        <style>
            :root {{
                --primary: #2563eb;
                --primary-light: #60a5fa;
                --bg: #f4f7ff;
                --card: #ffffff;
                --text: #0f172a;
                --muted: #64748b;
                --border: #e2e8f5;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                background: var(--bg);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                color: var(--text);
                padding-bottom: 60px;
            }}
            .hero {{
                background: linear-gradient(135deg, #2563eb, #38bdf8);
                color: #fff;
                padding: 64px 24px 48px;
                text-align: center;
            }}
            .hero h1 {{
                margin: 0 0 8px;
                font-size: 2em;
                letter-spacing: -0.5px;
            }}
            .hero p {{
                margin: 0;
                opacity: 0.9;
            }}
            .container {{
                max-width: 640px;
                margin: -28px auto 0;
                padding: 0 20px;
            }}
            .card {{
                background: var(--card);
                border-radius: 20px;
                box-shadow: 0 12px 32px rgba(37, 99, 235, 0.12);
                padding: 28px;
                margin-bottom: 28px;
            }}
            .card h2 {{
                margin: 0 0 18px;
                font-size: 1.1em;
                color: var(--primary);
            }}
            .field-row {{
                display: flex;
                gap: 12px;
                margin-bottom: 12px;
            }}
            input, textarea {{
                width: 100%;
                font-size: 0.95em;
                padding: 12px 14px;
                border-radius: 12px;
                border: 1px solid var(--border);
                background: #f8faff;
                color: var(--text);
                outline: none;
                font-family: inherit;
                transition: border-color 0.15s, box-shadow 0.15s;
            }}
            input:focus, textarea:focus {{
                border-color: var(--primary-light);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
            }}
            textarea {{
                resize: vertical;
                min-height: 90px;
                margin-bottom: 16px;
            }}
            .submit-btn {{
                display: block;
                width: 100%;
                padding: 13px;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #2563eb, #38bdf8);
                color: #fff;
                font-size: 1em;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.15s, box-shadow 0.15s;
            }}
            .submit-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
            }}
            .error {{
                color: #dc2626;
                font-size: 0.85em;
                margin: -6px 0 12px;
            }}
            .count {{
                color: var(--muted);
                font-size: 0.85em;
                margin: 0 4px 12px;
            }}
            .entry-list {{
                list-style: none;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                gap: 14px;
            }}
            .entry {{
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 18px 20px;
                transition: box-shadow 0.15s, transform 0.15s;
            }}
            .entry:hover {{
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.1);
                transform: translateY(-2px);
            }}
            .entry-head {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 10px;
            }}
            .avatar {{
                width: 38px;
                height: 38px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-weight: 700;
                flex-shrink: 0;
            }}
            .entry-meta {{
                display: flex;
                flex-direction: column;
                flex: 1;
            }}
            .entry-name {{
                font-weight: 700;
                font-size: 0.95em;
            }}
            .entry-date {{
                font-size: 0.75em;
                color: var(--muted);
            }}
            .entry-message {{
                margin: 0;
                line-height: 1.6;
                word-break: break-word;
                white-space: pre-wrap;
            }}
            .delete-toggle {{
                position: relative;
            }}
            .delete-toggle summary {{
                list-style: none;
                cursor: pointer;
                font-size: 0.78em;
                color: var(--muted);
                padding: 4px 10px;
                border-radius: 8px;
            }}
            .delete-toggle summary:hover {{
                background: #f1f5ff;
                color: var(--primary);
            }}
            .delete-toggle summary::-webkit-details-marker {{ display: none; }}
            .delete-form {{
                position: absolute;
                right: 0;
                top: 30px;
                background: #fff;
                border: 1px solid var(--border);
                border-radius: 12px;
                box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
                padding: 10px;
                display: flex;
                gap: 6px;
                z-index: 10;
                width: 200px;
            }}
            .delete-form input {{
                padding: 8px 10px;
                font-size: 0.85em;
            }}
            .delete-form button {{
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
                background: var(--primary);
                color: #fff;
                font-size: 0.85em;
                cursor: pointer;
                flex-shrink: 0;
            }}
            .empty {{
                text-align: center;
                color: var(--muted);
                padding: 40px 0;
            }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>💙 방명록</h1>
            <p>다녀가신 흔적을 남겨주세요</p>
        </div>
        <div class="container">
            <div class="card">
                <h2>글 남기기</h2>
                <form method="post" action="/entries">
                    <div class="field-row">
                        <input type="text" name="name" placeholder="이름 / 닉네임" maxlength="20" required>
                        <input type="password" name="password" placeholder="비밀번호 (삭제 시 필요)" maxlength="30" required>
                    </div>
                    <textarea name="message" placeholder="남기실 말씀을 적어주세요" maxlength="500" required></textarea>
                    {error_html}
                    <button type="submit" class="submit-btn">등록하기</button>
                </form>
            </div>
            <p class="count">총 {len(entries)}개의 방명록</p>
            {list_html}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def index():
    return render_page(load_entries())


@app.post("/entries", response_class=HTMLResponse)
def create_entry(
    request: Request,
    name: str = Form(...),
    password: str = Form(...),
    message: str = Form(...),
):
    name = name.strip()
    message = message.strip()

    if not name or not password or not message:
        return render_page(load_entries(), error="이름, 비밀번호, 내용을 모두 입력해주세요.")

    entries = load_entries()
    entries.append(
        {
            "id": uuid.uuid4().hex,
            "name": name[:20],
            "message": message[:500],
            "password_hash": hash_password(password),
            "ip": request.client.host if request.client else "",
            "created_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        }
    )
    save_entries(entries)
    return RedirectResponse("/", status_code=303)


@app.post("/entries/{entry_id}/delete", response_class=HTMLResponse)
def delete_entry(entry_id: str, password: str = Form(...)):
    entries = load_entries()
    target = next((e for e in entries if e["id"] == entry_id), None)

    if target is None or target["password_hash"] != hash_password(password):
        return render_page(load_entries(), error="비밀번호가 일치하지 않습니다.")

    entries = [e for e in entries if e["id"] != entry_id]
    save_entries(entries)
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
