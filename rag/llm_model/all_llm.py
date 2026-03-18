from langchain_openai import ChatOpenAI

from utils.load_env import OPENAI_API_KEY, OPENAI_BASE_URL, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

openai_llm = ChatOpenAI(
    model='gpt-4o-mini',
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

deepseek_llm = ChatOpenAI(
    temperature=0.5,
    model='deepseek-chat',
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)
