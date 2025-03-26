import logging
import asyncio
import numpy as np
from scipy.signal import resample
from RealtimeSTT import AudioToTextRecorder
import json

logger = logging.getLogger(__name__)

class STTService:
    """Service for handling speech-to-text using RealtimeSTT."""
    
    def __init__(self):
        """Initialize the STT service with default configuration."""
        self.recorder = None
        self.initialize_recorder()
        self.is_recording = False
        self.realtime_text = ""
        
    def initialize_recorder(self, model="medium", language="en"):
        """Initialize or reinitialize the recorder with specified parameters."""
        try:
            logger.info(f"Initializing STT recorder with model: {model}")
            
            self.recorder_config = {
                'spinner': False,
                'use_microphone': False,
                'model': model,
                'language': language,
                'silero_sensitivity': 0.4,
                'webrtc_sensitivity': 2,
                'post_speech_silence_duration': 0.7,
                'min_length_of_recording': 0,
                'min_gap_between_recordings': 0,
                'enable_realtime_transcription': True,
                'realtime_processing_pause': 0,
                'realtime_model_type': 'tiny.en',
                'on_realtime_transcription_stabilized': self.on_text_detected,
            }
            
            self.recorder = AudioToTextRecorder(**self.recorder_config)
            logger.info("STT recorder initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize STT recorder: {e}")
            return False
    
    def on_text_detected(self, text):
        """Handle real-time text detection from recorder."""
        self.realtime_text = text
        logger.debug(f"Real-time text detected: {text}")
    
    def decode_and_resample(self, audio_data, original_sample_rate, target_sample_rate=16000):
        """Decode and resample audio data for processing."""
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            num_original_samples = len(audio_np)
            num_target_samples = int(num_original_samples * target_sample_rate / original_sample_rate)
            resampled_audio = resample(audio_np, num_target_samples)
            return resampled_audio.astype(np.int16).tobytes()
        except Exception as e:
            logger.error(f"Error in resampling: {e}")
            return audio_data
    
    def feed_audio(self, audio_data, metadata=None):
        """Feed audio data to the recorder."""
        if self.recorder:
            try:
                if metadata:
                    sample_rate = metadata.get('sampleRate', 16000)
                    audio_data = self.decode_and_resample(audio_data, sample_rate)
                self.recorder.feed_audio(audio_data)
                return True
            except Exception as e:
                logger.error(f"Error feeding audio to recorder: {e}")
        return False
    
    def get_text(self):
        """Get the full sentence from the recorder."""
        if self.recorder:
            try:
                return self.recorder.text()
            except Exception as e:
                logger.error(f"Error getting text from recorder: {e}")
        return None
    
    def get_realtime_text(self):
        """Get the current real-time text."""
        return self.realtime_text
    
    def reset(self):
        """Reset the recorder state."""
        self.realtime_text = ""
    
    def get_available_models(self):
        """Get a list of available STT models."""
        return [
            "tiny.en", 
            "tiny", 
            "base.en", 
            "base", 
            "small.en", 
            "small", 
            "medium.en", 
            "medium", 
            "large-v2",
            "large-v3"
        ]
