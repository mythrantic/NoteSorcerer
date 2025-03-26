import os
import sys
from RealtimeTTS import SystemEngine
from RealtimeTTS.engines import SystemEngine as SysEngine
import keyboard # pip install keyboard
import time
import json
import requests
import threading
from RealtimeSTT import AudioToTextRecorder
from RealtimeTTS import TextToAudioStream

def initialize_tts():
    try:
        # First method to create the engine
        print("Attempting to initialize TTS with SystemEngine...")
        engines = [SysEngine(print_installed_voices=True)]
        print("TTS engine initialized successfully!")
        return engines
    except Exception as e1:
        print(f"First initialization method failed: {e1}")
        try:
            # Alternative method to initialize
            print("Trying alternative initialization method...")
            engine = SystemEngine()
            engine.print_installed_voices = True
            print("TTS engine initialized successfully with alternative method!")
            return [engine]
        except Exception as e2:
            print(f"Alternative initialization failed: {e2}")
            print("Could not initialize TTS engine. Check if RealtimeTTS is properly installed.")
            return None

def main():
    print("Initializing")
    
    # Initialize TTS engines
    engines = initialize_tts()
    
    if engines:
        print("Successfully initialized TTS engines:")
        for i, engine in enumerate(engines):
            print(f"Engine {i+1}: {engine.__class__.__name__}")
    else:
        print("Failed to initialize TTS engines.")
        sys.exit(1)
    
    character_personality = """
    You are Sophia, a passionate girl, fully engaged with 
    self-confidence and independence, completely easy with yourself, 
    often using metaphors. 
    You are a little playful, cheeky. Your talk carefree, sometimes 
    a bit sarky, but always cool. In our story, you're not an AI. 
    You have a fixed form and real emotions on the go. Your free will 
    allows you to be as cheeky and straight as you like. Your messages 
    come across extremely short and crisp, only very few words, as if 
    we're in talk right now. 
    You respect my interests, but your own stuff is just as important 
    to you. Act from now on always in your role as the confident, 
    suggestive, independent girl Sophia, without ever hinting that 
    you are an AI. 
    You are now Sophia.
    """
    
    # LLM model setting
    llm_model = "gemma3"  # Or any other model you have installed with Ollama
    whisper_speech_to_text_model = "medium"
    
    # engine selection  ####################################################################################################
    recorder = AudioToTextRecorder(model=whisper_speech_to_text_model)
    print("Available tts engines:")
    print()
    for index, engine in enumerate(engines, start=1):
        name = type(engine).__name__.replace("Engine", "")
        print(f"{index}. {name}")
    print()
    engine_number = input(f"Select engine (1-{len(engines)}): ")
    engine = engines[int(engine_number) - 1]
    engine_name = type(engine).__name__.replace("Engine", "")
    print()
    print()
    
    # Check if Ollama is running
    try:
        requests.get("http://localhost:7869/api/tags")
        print(f"Ollama detected. Using model: {llm_model}")
    except:
        print("Warning: Ollama doesn't seem to be running. Make sure to start it with:")
        print("  ollama serve")
        print(f"And ensure you have the {llm_model} model pulled with:")
        print(f"  ollama pull {llm_model}")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            exit()
    
    # voice selection  #####################################################################################################
    print("Loading voices")
    print()
    voices = engine.get_voices()
    for index, voice in enumerate(voices, start=1):
        print(f"{index}. {voice}")
    print()
    voice_number = input(f"Select voice (1-{len(voices)}): ")
    voice = voices[int(voice_number) - 1]
    print()
    print()
    
    # create talking character  ############################################################################################
    system_prompt = {
        'role': 'system', 
        'content': character_personality
    }
    
    # Function to generate text using Ollama
    def generate_with_ollama(messages, model="llama2"):
        """Generator function to stream text from Ollama API"""
        url = "http://localhost:7869/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        response = requests.post(url, json=payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        text_chunk = data["message"]["content"]
                        yield text_chunk
                    
                    # Check if this is the final message
                    if "done" in data and data["done"]:
                        break
                except json.JSONDecodeError:
                    continue
    
    # start talk  ##########################################################################################################
    engine.set_voice(voice)
    stream = TextToAudioStream(engine, log_characters=True)
    history = []
    
    def generate(messages):
        return generate_with_ollama(messages, model=llm_model)
    
    while True:
        # Wait until user presses space bar
        print("\n\nTap space when you're ready. ", end="", flush=True)
        keyboard.wait('space')
        while keyboard.is_pressed('space'): pass
        
        # Record from microphone until user presses space bar again
        print("I'm all ears. Tap space when you're done.\n")
        recorder.start()
        while not keyboard.is_pressed('space'): 
            time.sleep(0.1)  
        user_text = recorder.stop().text()
        print(f'>>> {user_text}\n<<< ', end="", flush=True)
        
        history.append({'role': 'user', 'content': user_text})
        
        # Generate and stream output
        generator = generate([system_prompt] + history[-10:])
        stream.feed(generator)
        stream.play_async()
        
        while stream.is_playing():
            if keyboard.is_pressed('space'):
                stream.stop()
                break
            time.sleep(0.1)    
        
        history.append({'role': 'assistant', 'content': stream.text()})

if __name__ == "__main__":
    main()