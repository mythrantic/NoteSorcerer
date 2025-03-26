import uvicorn
import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_service import LLMService
from controllers.conversation_controller import ConversationController

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="NoteSorcerer")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
stt_service = STTService()
tts_service = TTSService()
llm_service = LLMService()

# Initialize controller
conversation_controller = ConversationController(stt_service, llm_service, tts_service)

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time conversation."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        await conversation_controller.handle_conversation(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.close(code=1011, reason="Server error")

@app.get("/health")
async def health_check():
    """Check if the app is running."""
    return {"status": "healthy"}

@app.get("/available-engines")
async def get_available_engines():
    """Get all available TTS engines."""
    return {
        "tts_engines": tts_service.get_available_engines(),
        "stt_models": stt_service.get_available_models(),
        "llm_models": llm_service.get_available_models()
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8001))
    
    # Start server
    logger.info(f"Starting NoteSorcerer on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
