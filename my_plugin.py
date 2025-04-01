
import subprocess
import os
from logspyq.api import LogseqPlugin
import pygame
from voice_sevice import VoiceService
import asyncio
from ai_assistant import AIVoiceAssistant

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
    # Register a slash command


@logseq.Editor.registerSlashCommand("phi")
async def phi(sid):
    print("phi Command was executed")

    await logseq.App.showMsg("🎉🎉phi Command was executed🎉🎉")
    # text = await logseq.Editor.getEditingBlockContent()  #text
    text = await logseq.Editor.getCurrentBlock()  # text.content
    vc = VoiceService(
        mp3_filename="hello.mp3",
        vtt_filename="hello.vtt"
    )
    # await vc.play_tts_module(text=text.content)
    ai = AIVoiceAssistant()
    user_input_transcription = "User: " + text.content + "\n"
    output = ai.interact_with_llm(user_input_transcription)

    vc.play_tts_terminal(text=output, voice="en-US-MichelleNeural")
if __name__ == "__main__":
    logseq.run(host="localhost", port=8484, debug=True)
