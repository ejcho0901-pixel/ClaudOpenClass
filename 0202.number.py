import random
import uuid

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
games = {}


STATUS_META = {
    "start": {"icon": "🎯", "class": "status-start"},
    "up": {"icon": "⬆️", "class": "status-up"},
    "down": {"icon": "⬇️", "class": "status-down"},
    "win": {"icon": "🎉", "class": "status-win"},
}


def render(message: str, tries: int, finished: bool, status: str = "start") -> str:
    meta = STATUS_META[status]

    input_box = (
        ""
        if finished
        else """
        <form method="post" action="/guess" class="guess-form">
            <input type="number" name="guess" min="1" max="100" placeholder="1 ~ 100" autofocus required>
            <button type="submit">확인</button>
        </form>
        """
    )
    restart = '<a href="/" class="restart-btn">다시 도전하기</a>' if finished else ""

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>숫자 맞추기 게임</title>
        <style>
            :root {{
                --up: #3b82f6;
                --down: #f97316;
                --win: #22c55e;
                --start: #a78bfa;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                background-size: 200% 200%;
                animation: bgshift 12s ease infinite;
                padding: 24px;
            }}
            @keyframes bgshift {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
            .card {{
                width: 100%;
                max-width: 420px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 24px;
                backdrop-filter: blur(16px);
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
                padding: 40px 32px;
                text-align: center;
                color: #f5f5f7;
            }}
            h1 {{
                font-size: 1.4em;
                margin: 0 0 8px;
                letter-spacing: 0.5px;
                color: #ffffff;
            }}
            .subtitle {{
                margin: 0 0 28px;
                color: rgba(255, 255, 255, 0.55);
                font-size: 0.85em;
            }}
            .icon {{
                font-size: 3.2em;
                margin-bottom: 8px;
                display: inline-block;
                animation: pop 0.4s ease;
            }}
            @keyframes pop {{
                0% {{ transform: scale(0.5); opacity: 0; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
            .message {{
                font-size: 1.3em;
                font-weight: 700;
                margin: 4px 0 24px;
            }}
            .status-start .message {{ color: var(--start); }}
            .status-up .message {{ color: var(--up); }}
            .status-down .message {{ color: var(--down); }}
            .status-win .message {{
                background: linear-gradient(90deg, #22c55e, #a3e635);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
            }}
            .tries {{
                display: inline-block;
                padding: 6px 16px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.12);
                font-size: 0.85em;
                margin-bottom: 28px;
                color: rgba(255, 255, 255, 0.8);
            }}
            .guess-form {{
                display: flex;
                gap: 10px;
            }}
            input[type="number"] {{
                flex: 1;
                font-size: 1.1em;
                padding: 12px 16px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(0, 0, 0, 0.25);
                color: #fff;
                outline: none;
                transition: border-color 0.2s, box-shadow 0.2s;
            }}
            input[type="number"]:focus {{
                border-color: var(--up);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
            }}
            input[type="number"]::-webkit-outer-spin-button,
            input[type="number"]::-webkit-inner-spin-button {{
                -webkit-appearance: none;
                margin: 0;
            }}
            button {{
                font-size: 1.05em;
                font-weight: 600;
                padding: 12px 22px;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: #fff;
                cursor: pointer;
                transition: transform 0.15s, box-shadow 0.15s;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
            }}
            .restart-btn {{
                display: inline-block;
                margin-top: 4px;
                padding: 12px 24px;
                border-radius: 12px;
                background: linear-gradient(135deg, #22c55e, #16a34a);
                color: #fff;
                text-decoration: none;
                font-weight: 600;
                transition: transform 0.15s, box-shadow 0.15s;
            }}
            .restart-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(34, 197, 94, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="card {meta['class']}">
            <h1>1 ~ 100 숫자 맞추기</h1>
            <p class="subtitle">적은 횟수로 맞출수록 고득점!</p>
            <div class="icon">{meta['icon']}</div>
            <p class="message">{message}</p>
            <div class="tries">시도 횟수 · {tries}</div>
            {input_box}
            {restart}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def new_game():
    session_id = str(uuid.uuid4())
    games[session_id] = {"answer": random.randint(1, 100), "tries": 0}

    html = render("1부터 100 사이의 숫자를 맞춰보세요!", 0, finished=False, status="start")
    response = HTMLResponse(html)
    response.set_cookie("session_id", session_id)
    return response


@app.post("/guess", response_class=HTMLResponse)
def guess(request: Request, guess: int = Form(...)):
    session_id = request.cookies.get("session_id")
    game = games.get(session_id)

    if game is None:
        return RedirectResponse("/", status_code=303)

    game["tries"] += 1
    answer = game["answer"]

    if guess < answer:
        message, finished, status = "UP! 더 큰 숫자예요", False, "up"
    elif guess > answer:
        message, finished, status = "DOWN! 더 작은 숫자예요", False, "down"
    else:
        message = f"정답입니다! {game['tries']}번 만에 맞추셨습니다. 축하합니다!"
        finished, status = True, "win"
        del games[session_id]

    return render(message, game["tries"], finished, status=status)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
