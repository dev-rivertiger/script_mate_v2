from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import json
from pathlib import Path

app = FastAPI()

# [보안] 세션 미들웨어 설정: 사용자별 독립적인 연습 환경 보장
# 'secret_key'는 본인만 아는 랜덤한 문자열로 변경하세요.
app.add_middleware(SessionMiddleware, secret_key="script_mate_v2_2026_key_unique")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
SCRIPT_DIR = os.path.join(BASE_DIR, "scripts")

# 1. 메인 홈 화면
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# 2. 배역 선택 화면 (라디오 버튼 방식)
@app.get("/select", response_class=HTMLResponse)
async def select_role(request: Request):
    # scripts 폴더 존재 확인 및 파일 목록 가져오기
    if not os.path.exists(SCRIPT_DIR):
        return HTMLResponse(f"에러: {SCRIPT_DIR} 폴더가 없습니다. 폴더를 생성하고 대본을 넣어주세요.")

    files = [f for f in os.listdir(SCRIPT_DIR) if f.endswith("_numbering.txt")]
    if not files:
        return HTMLResponse("대본 파일(_numbering.txt)이 scripts 폴더에 없습니다.")

    # 첫 번째 대본을 기준으로 배역 추출
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

# 3. 연습 화면 (세션 데이터 반영)
@app.post("/practice", response_class=HTMLResponse)
async def practice(
    request: Request, 
    filename: str = Form(...), 
    role: str = Form(...)  # select_role.html의 라디오 버튼 'name="role"'과 일치
):
    # 사용자의 선택 배역을 세션에 저장 (서버 측 사용자 구별)
    request.session["my_role"] = role
    request.session["filename"] = filename

    file_path = os.path.join(SCRIPT_DIR, filename)
    script_data = []

    # 대본 데이터를 다시 읽어와서 전달
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

    return templates.TemplateResponse("practice.html", {
        "request": request,
        "script": script_data,
        "my_roles": [role], # JS 로직 호환성을 위해 리스트로 전달
        "filename": filename
    })