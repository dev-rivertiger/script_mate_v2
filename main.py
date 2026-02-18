from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import json
import hashlib
import asyncio
from pathlib import Path

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="script_mate_v2_2026_key_unique")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
SCRIPT_DIR = os.path.join(BASE_DIR, "scripts")
TTS_CACHE_DIR = os.path.join(BASE_DIR, "tts_cache")

os.makedirs(TTS_CACHE_DIR, exist_ok=True)

# 한국어 음성 정의
VOICES = {
    "female": "ko-KR-SunHiNeural",
    "male": "ko-KR-InJoonNeural",
}

# ============================================
# TTS 엔드포인트 (Edge TTS)
# ============================================
@app.get("/tts")
async def tts_endpoint(text: str, gender: str = "female", speed: float = 1.2):
    """Edge TTS로 한국어 음성 생성 후 mp3 반환 (남/여 선택, 속도 조절, 캐시)"""
    try:
        import edge_tts
        
        # 음성 선택
        voice = VOICES.get(gender, VOICES["female"])
        
        # 속도를 edge-tts rate 포맷으로 변환 (1.0 = +0%, 1.5 = +50%, 0.5 = -50%)
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
        
        # 캐시 키 (텍스트 + 성별 + 속도)
        cache_key = hashlib.md5(f"{text}_{gender}_{rate_str}".encode('utf-8')).hexdigest()
        cache_path = os.path.join(TTS_CACHE_DIR, f"{cache_key}.mp3")
        
        # 캐시에 없으면 생성
        if not os.path.exists(cache_path):
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate_str)
            await communicate.save(cache_path)
        
        return FileResponse(
            cache_path, 
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except ImportError:
        return JSONResponse(
            {"error": "edge-tts 미설치. pip install edge-tts 실행 필요"},
            status_code=500
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================
# 페이지 라우트
# ============================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/select", response_class=HTMLResponse)
async def select_role(request: Request, mode: str = "practice"):
    if not os.path.exists(SCRIPT_DIR):
        return HTMLResponse(f"에러: {SCRIPT_DIR} 폴더가 없습니다.")

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


@app.post("/practice", response_class=HTMLResponse)
async def practice(
    request: Request, 
    filename: str = Form(...), 
    role: str = Form(...),
    mode: str = Form("practice"),
    colors: str = Form("{}"),
    genders: str = Form("{}"),
    tts_enabled: str = Form("false"),
    tts_speed: str = Form("1.2")
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
                script_data.append({"idx": idx_part, "role": role_name, "text": text})

    template_name = "view.html" if mode == "view" else "practice.html"
    
    return templates.TemplateResponse(template_name, {
        "request": request,
        "script": script_data,
        "my_roles": [role],
        "filename": filename,
        "mode": mode,
        "colors": colors,
        "genders": genders,
        "tts_enabled": tts_enabled,
        "tts_speed": tts_speed
    })


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🎭 Script Mate 서버 시작!")
    print("=" * 60)
    print("브라우저: http://localhost:8000")
    print("모바일: http://[컴퓨터IP]:8000")
    print("종료: Ctrl + C")
    print("=" * 60)
    print("💡 필수: pip install edge-tts")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
