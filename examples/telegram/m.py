
from logspyq.api import LogseqPlugin
from pyllamacpp.model import Model


#
from huggingface_hub import hf_hub_download
from pyllamacpp.model import Model

from langchain import PromptTemplate, LLMChain
from langchain.llms import GPT4All, LlamaCpp
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.embeddings import LlamaCppEmbeddings
template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

# Llama-cpp: https://python.langchain.com/en/latest/modules/models/llms/integrations/llamacpp.html
try:
    hf_hub_download(repo_id="botato/point-alpaca-ggml-model-q4_0", filename="ggml-model-q4_0.bin", local_dir=".")
except:
    pass
llm = LlamaCpp(model_path="./ggml-model-q4_0.bin")
llm_chain = LLMChain(prompt=prompt, llm=llm)

"""
# Embedding with llama: https://python.langchain.com/en/latest/modules/models/text_embedding/examples/llamacpp.html
llama = LlamaCppEmbeddings(model_path="./ggml-model-q4_0.bin")
text = "This is a test document."
query_result = llama.embed_query(text)
doc_result = llama.embed_documents([text])
print(query_result)
print(doc_result)
# Store in db, Chroma DB
# Next : https://www.youtube.com/watch?v=LbT1yp6quS8&t=29s
"""

logseq = LogseqPlugin(name="Hello Agent", description="Say hello to Logseq")



@logseq.Editor.registerSlashCommand("ok")
async def hello(sid):
    current_block = await logseq.Editor.getCurrentBlock()
    try: 
    
        #Generate
        question = await logseq.Editor.getEditingBlockContent()
        print(question)

       
        result= llm_chain.run(question)
        print(result)
        
        #
        
        '''properties = {
                "link": "localhost",
                "description": "mai model",
                "source": "llama",
            }'''
        await logseq.Editor.insertBlock(current_block.uuid, f"\nMAI: {result}", sibling=False) # properties=properties,
    except Exception as e:
        await logseq.Editor.insertBlock(current_block.uuid, f"\nFailure: {e}", sibling=False)
       

if __name__ == "__main__":
    logseq.run(host="localhost", port=8484, debug=True)


