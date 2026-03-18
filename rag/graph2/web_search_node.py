from langchain_community.tools import TavilySearchResults
from langchain_core.documents import Document

from utils.log_utils import log


def web_search(state):
    """
    基于优化后的问题进行网络搜索

    Args:
        state (dict): 当前图状态，包含优化后的问题

    Returns:
        state (dict): 更新后的状态，documents字段替换为网络搜索结果
    """
    log.info('---使用互联网搜索---')
    question = state['question']

    web_search_tool = TavilySearchResults(max_results=1)
    docs = web_search_tool.invoke({"query": question})
    web_results = '\n'.join([d['content'] for d in docs])
    web_results = Document(page_content=web_results)

    return {'documents': web_results, 'question': question}

