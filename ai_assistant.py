from langchain.chains import ConversationalRetrievalChain, create_retrieval_chain, create_history_aware_retriever
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain


from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains import ConversationalRetrievalChain, create_retrieval_chain, create_history_aware_retriever

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.llms.ollama import Ollama


class AIVoiceAssistant:
    def __init__(self):
        self._embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2")
        self._vector_store = Chroma(
            collection_name="kitchen_db", embedding_function=self._embedding_model)
        self._llm = Ollama(
            model="gemma3", base_url="https://ollama.valiantlynx.com")
        self._create_kb()
        self._create_chains()

    def _create_kb(self):
        loader = DirectoryLoader(
            r"/home/valiantlynx/valiantlynx_logseq/pages", glob="**/*.md", show_progress=True)
        documents = loader.load()
        self._vector_store.add_documents(documents)
        print("Knowledgebase created successfully!")

    def _create_chains(self):
        retriever = self._vector_store.as_retriever()

        # Create the question generation chain
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Given a chat history and the latest user question which might reference context in the chat history, "
                           "formulate a standalone question which can be understood without the chat history. Do NOT answer the question, "
                           "just reformulate it if needed and otherwise return it as is."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self._llm, retriever, contextualize_q_prompt
        )

        # Create the question-answer chain
        qa_system_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. "
                           "If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\n\n"
                           "{context}"),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(
            self._llm, qa_system_prompt)

        # Create the final conversational retrieval chain
        self._retriever = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

    def interact_with_llm(self, customer_query):
        response = self._retriever.invoke(
            {"input": customer_query, "chat_history": []})
        return response["answer"]
