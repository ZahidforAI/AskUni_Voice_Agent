import asyncio
import json
import re
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from groq_rag import get_groq_response, create_vector_db

app = FastAPI()

# Ensure vector database exists
DB_PATH = "./faiss_index"

# ============================================================================
# URL Mappings
# ============================================================================
SMIU_URLS = {
    "home": "https://smiu.edu.pk/", "admission": "https://smiu.edu.pk/admissions",
    "programs": "https://www.smiu.edu.pk/admissions/undergraduate-programs",
    "fee": "https://smiu.edu.pk/admissions/fee-structure", "portal": "http://cms.smiu.edu.pk:9991/psp/ps/?cmd=login"
}
NED_URLS = {
    "home": "https://www.neduet.edu.pk/", "admission": "https://www.neduet.edu.pk/admissions",
    "fee": "https://www.neduet.edu.pk/fee-structure"
}
IBA_URLS = {
    "home": "https://www.iba.edu.pk/", "admission": "https://www.iba.edu.pk/admissions.php",
    "fee": "https://www.iba.edu.pk/fee-structure.php"
}
UOK_URLS = {
    "home": "https://www.uok.edu.pk/", "admission": "https://uokadmission.edu.pk/",
    "fee": "https://www.uok.edu.pk/admission/fee_structure.php"
}
FAST_URLS = {
    "home": "https://khi.nu.edu.pk/", "admission": "https://admissions.nu.edu.pk/",
    "fee": "https://khi.nu.edu.pk/Admissions/FeeStructure"
}
SZABIST_URLS = {
    "home": "https://szabist.edu.pk/", "admission": "https://admissions.szabist.edu.pk/",
    "fee": "https://szabist.edu.pk/fee-structure"
}
DHA_SUFFA_URLS = {
    "home": "https://www.dsu.edu.pk/", "admission": "https://www.dsu.edu.pk/admissions/",
    "fee": "https://www.dsu.edu.pk/admissions/fee-structure/"
}
DUET_URLS = {
    "home": "https://duet.edu.pk/", "admission": "https://admissions.duet.edu.pk/",
    "fee": "https://duet.edu.pk/fee-structure/"
}

NAVIGATION_KEYWORDS = ["open", "go to", "take me to", "show me", "navigate to", "visit"]

def clean_text_for_tts(text):
    if not text: return ""
    text = re.sub(r'[_\-=*]{3,}', '', text)
    return text.replace('**', '').replace('__', '').strip()

def detect_navigation_request(text):
    text_lower = text.lower().strip()
    is_navigation = any(keyword in text_lower for keyword in NAVIGATION_KEYWORDS)
    if not is_navigation: return False, None, None, None
    
    uni_map = {"ned": (NED_URLS, "NED"), "iba": (IBA_URLS, "IBA"), "uok": (UOK_URLS, "UOK"), "fast": (FAST_URLS, "FAST"), 
               "szabist": (SZABIST_URLS, "SZABIST"), "dsu": (DHA_SUFFA_URLS, "DHA Suffa"), "duet": (DUET_URLS, "DUET")}
    
    university_urls, university_name = SMIU_URLS, "SMIU"
    for code, (urls, name) in uni_map.items():
        if code in text_lower:
            university_urls, university_name = urls, name
            break
            
    for page_name, url in university_urls.items():
        if page_name in text_lower:
            return True, url, page_name, university_name
    return False, None, None, None

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            if data.get("type") == "query":
                user_text = data.get("text", "").strip()
                is_nav, url, page_name, uni_name = detect_navigation_request(user_text)
                if is_nav:
                    await websocket.send_json({"type": "navigate", "url": url, "page_name": page_name, "university": uni_name})
                    await websocket.send_json({"type": "response", "text": f"Opening the {page_name} for {uni_name}."})
                else:
                    await websocket.send_json({"type": "status", "status": "processing", "message": "Searching..."})
                    response = get_groq_response(user_text)
                    await websocket.send_json({"type": "response", "text": clean_text_for_tts(response)})
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except Exception: pass

if __name__ == "__main__":
    import uvicorn
    if not os.path.exists(DB_PATH): create_vector_db()
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
