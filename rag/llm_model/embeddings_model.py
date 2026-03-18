from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from utils.load_env import OPENAI_API_KEY, OPENAI_BASE_URL

qwen_embedding = HuggingFaceEmbeddings(
    model_name = 'Qwen/Qwen3-Embedding-0.6B',
    model_kwargs = {"device": "cpu"},
    encode_kwargs = {"normalize_embeddings": True}
)

openai_embedding = OpenAIEmbeddings(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)



