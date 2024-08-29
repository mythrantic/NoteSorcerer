from logspyq.api import LogseqPlugin
from pyllamacpp.model import Model


logseq = LogseqPlugin(name="Hello Agent", description="Say hello to Logseq")
#Load the model
model = Model(ggml_model=fr"D:\models\ggml-model.bin", n_ctx=512)
def new_text_callback(text: str):
    print(text, end="", flush=True)


@logseq.Editor.registerSlashCommand("ok")
async def hello(sid):
    
    
    

    
    #Generate
    prompt = await logseq.Editor.getEditingBlockContent()
    print(prompt)

    result=model.generate(str(prompt), n_predict=55, n_threads=8) # new_text_callback=new_text_callback
    print(result)
    
    #
    current_block = await logseq.Editor.getCurrentBlock()
    '''properties = {
            "link": "localhost",
            "description": "mai model",
            "source": "llama",
        }'''
    await logseq.Editor.insertBlock(current_block.uuid, f"\nMAI: {result}", sibling=False) # properties=properties,
    
    #await logseq.Editor.insertAtEditingCursor(f"\nMAI: {result}")
    


if __name__ == "__main__":
    logseq.run(host="localhost", port=8484, debug=True)
