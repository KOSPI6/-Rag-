from graph2.graph_state2 import GraphState
from tools.retriever_tools import retriever
from utils.log_utils import log



def retrieve(state: GraphState):
    """
    检索相关文档
    Args:
        state (dict): 当前图状态，包含用户问题

    Returns:
        state (dict): 更新后的状态，新增包含检索结果的documents字段
    """
    log.info('---去知识库中检索文档---')
    question = state['question']
    documents = retriever.invoke(question)
    return {'documents': documents, 'question': question}


