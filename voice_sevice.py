import os
import pygame
import subprocess
import edge_tts
import asyncio


class VoiceService:
    def __init__(self, mp3_filename="temp.mp3", vtt_filename="temp.vtt"):
        self.mp3_filename = mp3_filename
        self.vtt_filename = vtt_filename

    def play_tts_terminal(self, text, language='en', voice='en-US-AriaNeural', slow=False):
        # Run the edge-tts command
        try:
            subprocess.run(
                ["edge-tts", "--voice", voice, "--text", text,
                    "--write-media", self.mp3_filename, "--write-subtitles", self.vtt_filename],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(
                f"Conversion complete. MP3 file saved as {self.mp3_filename} and VTT subtitles saved as {self.vtt_filename}")
            # Initialize pygame for audio playback
            pygame.init()
            pygame.mixer.init()

            # Load and play the generated audio
            pygame.mixer.music.load(self.mp3_filename)
            pygame.mixer.music.play()

            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Clean up resources
            pygame.mixer.quit()
            pygame.quit()
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

        # Remove the generated files
        os.remove(self.mp3_filename)
        os.remove(self.vtt_filename)

    async def play_tts_module(self, text, language='en', voice='en-US-AriaNeural',  slow=False):
        async def _main():
            communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
            await communicate.save(self.mp3_filename)
        await _main()

        pygame.mixer.init()
        pygame.mixer.music.load(self.mp3_filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()

        os.remove(self.mp3_filename)
