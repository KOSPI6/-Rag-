from graph2.grader_chain import retriever_grader_chain
from graph2.graph_state2 import GraphState
from utils.log_utils import log


def grade_documents(state: GraphState):
    """
    评估检索到的文档与问题的相关性

    Args:
        state (dict): 当前图状态，包含问题和检索结果

    Returns:
        state (dict): 更新后的状态，documents字段仅保留相关文档
    """
    log.info('---评估检索到的文档与用户问题的相关性---')
    question = state['question']
    documents = state['documents']

    filtered_docs = []
    for d in documents:
        score = retriever_grader_chain.invoke({"question": question, "document": d.page_content})
        grade = score.binary_score
        if grade == 'yes':
            log.info(f'---文档与问题相关---')
            filtered_docs.append(d)
        else:
            log.info(f'---文档与问题无关,丢弃该文档---')
            continue
    return {'documents': filtered_docs, 'question': question}

