from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from graph2.graph_state2 import GraphState
from llm_model.all_llm import deepseek_llm
from utils.log_utils import log


def transform_query(state: GraphState):
    """
    优化用户问题，生成更合适的查询语句

    Args:
        state (dict): 当前图状态，包含用户问题和检索结果

    Returns:
        state (dict): 更新后的状态，question字段替换为优化后的问题
    """

    log.info('---优化查询语句---')
    question = state['question']
    documents = state['documents']
    transform_count = state.get('transform_count', 0)

    system = """作为问题重写器，您需要将输入问题转换为更适合向量数据库检索的优化版本。\n
         请分析输入问题并理解其背后的语义意图/真实含义。"""

    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "这是初始问题: \n\n {question} \n 请生成一个优化后的问题。"),
        ]
    )

    question_rewriter = re_write_prompt | deepseek_llm | StrOutputParser()

    better_question = question_rewriter.invoke({"question": question})
    return {'question': better_question, 'documents': documents, 'transform_count': transform_count + 1}
