import random
import uuid

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
games = {}


def render(message: str, tries: int, finished: bool) -> str:
    input_box = (
        ""
        if finished
        else """
        <form method="post" action="/guess">
            <input type="number" name="guess" min="1" max="100" autofocus required>
            <button type="submit">확인</button>
        </form>
        """
    )
    restart = '<p><a href="/">다시 시작</a></p>' if finished else ""

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>숫자 맞추기 게임</title>
        <style>
            body {{ font-family: sans-serif; max-width: 480px; margin: 60px auto; text-align: center; }}
            input {{ font-size: 1.2em; padding: 6px; width: 100px; }}
            button {{ font-size: 1.2em; padding: 6px 16px; }}
            .message {{ font-size: 1.4em; margin: 24px 0; }}
        </style>
    </head>
    <body>
        <h1>1~100 숫자 맞추기</h1>
        <p class="message">{message}</p>
        <p>시도 횟수: {tries}</p>
        {input_box}
        {restart}
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def new_game():
    session_id = str(uuid.uuid4())
    games[session_id] = {"answer": random.randint(1, 100), "tries": 0}

    html = render("1부터 100 사이의 숫자를 맞춰보세요!", 0, finished=False)
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
        message, finished = "UP", False
    elif guess > answer:
        message, finished = "DOWN", False
    else:
        message = f"정답입니다! {game['tries']}번 만에 맞추셨습니다. 축하합니다!"
        finished = True
        del games[session_id]

    return render(message, game["tries"], finished)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
