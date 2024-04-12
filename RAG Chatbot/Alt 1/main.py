from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import HuggingFaceHub

from langchain import PromptTemplate

from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

import pinecone
from pinecone import Pinecone, ServerlessSpec

from dotenv import load_dotenv
import os



class ChatBot():
    load_dotenv()
    loader = TextLoader('sample2.txt')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(
        chunk_size = 1000, chunk_overlap = 4
    )
    
    docs = text_splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings()
    
    """ pinecone.init(
        api_key = os.getenv('PINECONE_API_KEY'),
        environment = 'gcp-starter'
    ) """
    
    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY")
    )
    
    index_name = "langchain_demo"
    
    if index_name not in pinecone.list_indexes():
        pc.create_index(
            name = index_name, metric = "cosine", dimension = 768
        )
        docsearch = Pinecone.from_documents(docs, embeddings, index_name = index_name)
    else:
        docsearch =  Pinecone.from_existing_index(index_name, embeddings)
    
    
    repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    llm = HuggingFaceHub(
        repo_id = repo_id,
        model_kwargs = {
            "temperature" : 0.8,
            "top_p": 0.8,
            "top_k": 50
            },
        huggingfacehub_api_token=os.getenv('HUGGINGFACE_API_KEY') 
    )
    
    template = """
    You are a seer. These Human will ask you a questions about their life. Use following piece of context to answer the question. 
    If you don't know the answer, just say you don't know. 
    You answer with short and concise answer, no longer than2 sentences.

    Context: {context}
    Question: {question}
    Answer: 
    """
    
    prompt = PromptTemplate(templete = template, input_variables = ["context", "question"])
    
    rag_chain = (
        {
            "context" : docsearch.as_retriever(),
            "question" : RunnablePassthrough() 
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    