import logging
import asyncio
import os
from RealtimeTTS import TextToAudioStream, SystemEngine, AzureEngine, OpenAIEngine, ElevenlabsEngine
from queue import Queue

logger = logging.getLogger(__name__)

class TTSService:
    """Service for handling text-to-speech using RealtimeTTS."""
    
    def __init__(self):
        """Initialize the TTS service with system engine by default."""
        self.engines = {}
        self.voices = {}
        self.current_engine = None
        self.stream = None
        self.initialize_engines()
        
    def initialize_engines(self):
        """Initialize available TTS engines."""
        try:
            # Initialize system engine (always available)
            logger.info("Initializing System TTS engine")
            self.engines["system"] = SystemEngine()
            self.voices["system"] = self.engines["system"].get_voices()
            
            # Try to initialize Azure engine if credentials available
            azure_key = os.environ.get("AZURE_SPEECH_KEY")
            azure_region = os.environ.get("AZURE_SPEECH_REGION")
            if azure_key and azure_region:
                logger.info("Initializing Azure TTS engine")
                self.engines["azure"] = AzureEngine(azure_key, azure_region)
                self.voices["azure"] = self.engines["azure"].get_voices()
            
            # Try to initialize OpenAI engine
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                logger.info("Initializing OpenAI TTS engine")
                os.environ["OPENAI_API_KEY"] = openai_key
                self.engines["openai"] = OpenAIEngine()
                self.voices["openai"] = self.engines["openai"].get_voices()
            
            # Try to initialize Elevenlabs engine
            elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
            if elevenlabs_key:
                logger.info("Initializing Elevenlabs TTS engine")
                self.engines["elevenlabs"] = ElevenlabsEngine(elevenlabs_key)
                self.voices["elevenlabs"] = self.engines["elevenlabs"].get_voices()
            
            # Set default engine to system
            self.set_engine("system")
            logger.info("TTS engines initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS engines: {e}")
            return False
    
    def set_engine(self, engine_name):
        """Set the current TTS engine."""
        if engine_name not in self.engines:
            logger.warning(f"Engine {engine_name} not available")
            return False
        
        try:
            self.current_engine = self.engines[engine_name]
            
            if self.stream:
                self.stream.load_engine(self.current_engine)
            else:
                self.stream = TextToAudioStream(self.current_engine)
                
            # Set default voice for this engine
            if self.voices[engine_name]:
                self.current_engine.set_voice(self.voices[engine_name][0].name)
                
            logger.info(f"Set TTS engine to {engine_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set TTS engine: {e}")
            return False
    
    def set_voice(self, voice_name):
        """Set the voice for the current engine."""
        if not self.current_engine:
            logger.warning("No engine selected")
            return False
        
        try:
            self.current_engine.set_voice(voice_name)
            logger.info(f"Set voice to {voice_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
            return False
    
    async def synthesize_text(self, text, callback=None):
        """Synthesize text to speech and stream audio chunks to callback."""
        if not self.current_engine or not self.stream:
            logger.warning("TTS engine not initialized")
            return False
        
        try:
            audio_queue = Queue()
            
            def on_audio_chunk(chunk):
                audio_queue.put(chunk)
                if callback:
                    asyncio.create_task(callback(chunk))
            
            logger.info(f"Synthesizing text: {text[:30]}...")
            self.stream.feed(text)
            self.stream.play(on_audio_chunk=on_audio_chunk, muted=True)
            audio_queue.put(None)  # Signal end of stream
            
            return True
        except Exception as e:
            logger.error(f"Failed to synthesize text: {e}")
            return False
    
    def get_available_engines(self):
        """Get a list of available TTS engines."""
        return list(self.engines.keys())
    
    def get_available_voices(self, engine_name=None):
        """Get available voices for a specific engine or current engine."""
        if engine_name and engine_name in self.voices:
            return [voice.name for voice in self.voices[engine_name]]
        elif self.current_engine:
            engine_name = self.current_engine.engine_name
            return [voice.name for voice in self.voices[engine_name]]
        return []
