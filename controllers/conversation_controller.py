import logging
import json
import asyncio
from fastapi import WebSocket
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ConversationController:
    """Controller for managing conversations between STT, LLM, and TTS services."""
    
    def __init__(self, stt_service: STTService, llm_service: LLMService, tts_service: TTSService):
        """Initialize the controller with required services."""
        self.stt_service = stt_service
        self.llm_service = llm_service
        self.tts_service = tts_service
        self.conversation_history = []
        self.default_persona = """
        You are Sophia, a friendly and helpful assistant. You provide concise,
        helpful responses to questions. Keep your answers informative but brief.
        """
    
    async def handle_conversation(self, websocket: WebSocket):
        """Handle the WebSocket conversation flow."""
        try:
            # Initial setup
            await self._send_status(websocket, "Connected to server")
            
            # Get client preferences if any
            config = await self._get_client_config(websocket)
            
            # Main conversation loop
            while True:
                # Wait for audio data from client
                message = await websocket.receive_bytes()
                
                # Process the message (could be audio data or control message)
                await self._process_message(websocket, message, config)
                
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            await self._send_error(websocket, f"Server error: {str(e)}")
    
    async def _get_client_config(self, websocket: WebSocket):
        """Get configuration preferences from client."""
        try:
            await self._send_message(websocket, "status", "Waiting for configuration...")
            message = await websocket.receive_text()
            config = json.loads(message)
            
            # Apply configuration settings
            if "tts_engine" in config and config["tts_engine"] in self.tts_service.get_available_engines():
                self.tts_service.set_engine(config["tts_engine"])
                
            if "tts_voice" in config:
                self.tts_service.set_voice(config["tts_voice"])
                
            if "stt_model" in config:
                self.stt_service.initialize_recorder(model=config["stt_model"])
            
            if "llm_model" in config and config["llm_model"] in self.llm_service.get_available_models():
                self.llm_service.default_model = config["llm_model"]
            
            if "persona" in config and config["persona"].strip():
                self.default_persona = config["persona"]
                
            await self._send_status(websocket, "Configuration applied")
            return config
        except Exception as e:
            logger.error(f"Error getting client config: {e}")
            await self._send_error(websocket, "Failed to apply configuration")
            return {}
    
    async def _process_message(self, websocket: WebSocket, message_bytes, config):
        """Process incoming message from client."""
        try:
            # Check if it's a control message or audio data
            if len(message_bytes) < 100:  # Likely a control message, not audio
                try:
                    text_message = message_bytes.decode('utf-8')
                    control_data = json.loads(text_message)
                    
                    if control_data.get("type") == "stop":
                        await self._send_status(websocket, "Stopping current operation")
                        return
                    
                    if control_data.get("type") == "text_input":
                        user_text = control_data.get("text", "")
                        await self._process_text_input(websocket, user_text)
                        return
                        
                except:
                    # Not a valid control message, assume it's audio data
                    pass
            
            # Extract metadata (first 4 bytes for length, then JSON)
            metadata_length = int.from_bytes(message_bytes[:4], byteorder='little')
            metadata_json = message_bytes[4:4+metadata_length].decode('utf-8')
            metadata = json.loads(metadata_json)
            audio_chunk = message_bytes[4+metadata_length:]
            
            # Process audio data
            self.stt_service.feed_audio(audio_chunk, metadata)
            
            # Check for real-time text updates
            realtime_text = self.stt_service.get_realtime_text()
            if realtime_text:
                await self._send_message(websocket, "realtime_text", realtime_text)
            
            # Check for full transcriptions
            full_text = self.stt_service.get_text()
            if full_text:
                await self._process_text_input(websocket, full_text)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error(websocket, f"Error processing input: {str(e)}")
    
    async def _process_text_input(self, websocket: WebSocket, user_text):
        """Process text input and generate response."""
        try:
            # Send acknowledgment with transcribed text
            await self._send_message(websocket, "transcription", user_text)
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_text})
            
            # Prepare messages for LLM
            messages = [{"role": "system", "content": self.default_persona}]
            messages.extend(self.conversation_history[-10:])  # Last 10 messages for context
            
            # Generate response from LLM
            response_text = ""
            async for text_chunk in self.llm_service.generate_response(messages):
                response_text += text_chunk
                await self._send_message(websocket, "llm_chunk", text_chunk)
            
            # Store the complete response in history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            await self._send_message(websocket, "llm_complete", response_text)
            
            # Synthesize speech from the response
            await self._send_status(websocket, "Synthesizing speech...")
            
            async def send_audio_chunk(chunk):
                await self._send_audio(websocket, chunk)
            
            await self.tts_service.synthesize_text(response_text, send_audio_chunk)
            await self._send_status(websocket, "Speech synthesis complete")
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            await self._send_error(websocket, f"Error generating response: {str(e)}")
    
    async def _send_message(self, websocket: WebSocket, message_type, content):
        """Send a message to the client."""
        await websocket.send_json({
            "type": message_type,
            "content": content
        })
    
    async def _send_status(self, websocket: WebSocket, status_message):
        """Send a status update to the client."""
        await self._send_message(websocket, "status", status_message)
    
    async def _send_error(self, websocket: WebSocket, error_message):
        """Send an error message to the client."""
        await self._send_message(websocket, "error", error_message)
    
    async def _send_audio(self, websocket: WebSocket, audio_chunk):
        """Send an audio chunk to the client."""
        await websocket.send_bytes(audio_chunk)
