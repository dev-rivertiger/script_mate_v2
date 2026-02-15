from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import json
from pathlib import Path

app = FastAPI()

# [보안] 세션 미들웨어 설정
app.add_middleware(SessionMiddleware, secret_key="script_mate_v2_2026_key_unique")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
SCRIPT_DIR = os.path.join(BASE_DIR, "scripts")

# 1. 메인 홈 화면
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# 2. 배역 선택 화면
@app.get("/select", response_class=HTMLResponse)
async def select_role(request: Request, mode: str = "practice"):
    if not os.path.exists(SCRIPT_DIR):
        return HTMLResponse(f"에러: {SCRIPT_DIR} 폴더가 없습니다. 폴더를 생성하고 대본을 넣어주세요.")

    files = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(".txt")]
    if not files:
        return HTMLResponse("대본 파일(.txt)이 scripts 폴더에 없습니다.")

    filename = files[0]
    file_path = os.path.join(SCRIPT_DIR, filename)

    script_data = []
    roles_found = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                parts = line.split(" ", 1)
                idx_part = parts[0].strip("[]")
                content_part = parts[1]

                role_content = content_part.split(": ", 1)
                role = role_content[0].strip()
                text = role_content[1].strip() if len(role_content) > 1 else ""

                script_data.append({"idx": idx_part, "role": role, "text": text})

                if role != "(지문)":
                    for r in role.split(','):
                        roles_found.add(r.strip())

    return templates.TemplateResponse("select_role.html", {
        "request": request,
        "roles": sorted(list(roles_found)),
        "script": json.dumps(script_data),
        "filename": filename
    })

# 3. 연습 화면
@app.post("/practice", response_class=HTMLResponse)
async def practice(
    request: Request, 
    filename: str = Form(...), 
    role: str = Form(...),
    mode: str = Form("practice"),
    colors: str = Form("{}")
):
    request.session["my_role"] = role
    request.session["filename"] = filename

    file_path = os.path.join(SCRIPT_DIR, filename)
    script_data = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                parts = line.split(" ", 1)
                idx_part = parts[0].strip("[]")
                content_part = parts[1]

                role_content = content_part.split(": ", 1)
                role_name = role_content[0].strip()
                text = role_content[1].strip() if len(role_content) > 1 else ""

                script_data.append({
                    "idx": idx_part,
                    "role": role_name,
                    "text": text
                })

    # mode에 따라 다른 템플릿 사용
    template_name = "view.html" if mode == "view" else "practice.html"
    
    return templates.TemplateResponse(template_name, {
        "request": request,
        "script": script_data,
        "my_roles": [role],
        "filename": filename,
        "mode": mode,
        "colors": colors
    })

# ============================================
# 직접 실행 가능 (python main.py)
# ============================================
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🎭 Script Mate 서버 시작!")
    print("=" * 60)
    print("브라우저: http://localhost:8000")
    print("모바일: http://[컴퓨터IP]:8000")
    print("종료: Ctrl + C")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
