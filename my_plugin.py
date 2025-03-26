
import subprocess
import os
from logspyq.api import LogseqPlugin
import pygame

logseq = LogseqPlugin(name="My Plugin", description="My first Logseq Plugin")


# Register a keyboard shortcut
@logseq.App.registerCommandPalette("My Command", binding="ctrl+ø", label="My Command")
async def my_command(sid, event):
    print("Keyboard shortcut pressed")
    await logseq.App.showMsg("TODO page opened from Python!")
    todo_page = await logseq.Editor.getPage("TODO")
    await logseq.Editor.openInRightSidebar(todo_page.uuid)


# Register a slash command
@logseq.Editor.registerSlashCommand("My Slash Command")
async def my_slash_command(sid):
    print("My Slash Command was executed")

    await logseq.App.showMsg("🎉🎉My Slash Command was executed🎉🎉")
    # text = await logseq.Editor.getEditingBlockContent()  #text
    text = await logseq.Editor.getCurrentBlock()  # text.content
    mp3_filename = "hello.mp3"
    vtt_filename = "hello.vtt"
    # Run the edge-tts command
    try:
        subprocess.run(
            ["edge-tts", "--voice", 'en-US-MichelleNeural', "--text", text.content,
                "--write-media", mp3_filename, "--write-subtitles", vtt_filename],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(
            f"Conversion complete. MP3 file saved as {mp3_filename} and VTT subtitles saved as {vtt_filename}")
        # Initialize pygame for audio playback
        pygame.init()
        pygame.mixer.init()

        # Load and play the generated audio
        pygame.mixer.music.load(mp3_filename)
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
    os.remove(mp3_filename)
    os.remove(vtt_filename)


# Register a slash command
@logseq.Editor.registerSlashCommand("phi")
async def phi(sid):
    print("phi Command was executed")

    await logseq.App.showMsg("🎉🎉phi Command was executed🎉🎉")
    # text = await logseq.Editor.getEditingBlockContent()  #text
    text = await logseq.Editor.getCurrentBlock()  # text.content
    mp3_filename = "hello.mp3"
    vtt_filename = "hello.vtt"
    # Run the edge-tts command
    try:
        subprocess.run(
            ["edge-tts", "--voice", 'en-US-MichelleNeural', "--text", text.content,
                "--write-media", mp3_filename, "--write-subtitles", vtt_filename],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(
            f"Conversion complete. MP3 file saved as {mp3_filename} and VTT subtitles saved as {vtt_filename}")
        # Initialize pygame for audio playback
        pygame.init()
        pygame.mixer.init()

        # Load and play the generated audio
        pygame.mixer.music.load(mp3_filename)
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
    os.remove(mp3_filename)
    os.remove(vtt_filename)

if __name__ == "__main__":
    logseq.run(host="localhost", port=8484, debug=True)
