from pprint import pprint

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from draw_png import draw_graph

from graph2.generate_node2 import generate
from graph2.grade_answer_chain import answer_grader_chain
from graph2.grade_documents_node import grade_documents
from graph2.grade_hallucinations_chain import hallucination_grader_chain
from graph2.graph_state2 import GraphState
from graph2.query_route_chain import question_router_chain
from graph2.retriever_node import retrieve
from graph2.transform_query_node import transform_query
from graph2.web_search_node import web_search
from utils.log_utils import log


def route_question(state: GraphState):
    """
    路由问题到网络搜索或RAG流程
    :param state:当前图状态，包含用户问题
    :return:下一节点的名称（web_search或vectorstore）
    """
    log.info('---路由当前问题到网络搜索或RAG流程---')
    question = state['question']
    source = question_router_chain.invoke({"question": question})

    if source.datasource == 'web_search':
        log.info('---路由到网络搜索---')
        return 'websearch'
    elif source.datasource == 'vectorstore':
        log.info('---路由到RAG流程---')
        return 'vectorstore'

def decide_to_generate(state: GraphState):
    """
    决定是生成回答还是重新优化问题
    :param state: 当前图状态，包含问题和过滤后的文档
    :return: str 下一个节点的名称
    """
    log.info('---决定是生成回答还是重新优化问题---')
    filtered_documents = state['documents']
    transform_count = state.get('transform_count', 0)

    if not filtered_documents:
        if transform_count >= 2:
            log.info('---决策：所有文档与问题无关，并且已经循环了2次，转为web查询问题---')
            return 'websearch'
        log.info('---决策：所有文档与问题无关，将转换并重新生成问题---')
        return 'transform_query'
    else:
        log.info('---决策：生成最终回答---')
        return 'generate'

def grade_generation_v_documents_and_question(state: GraphState):
    """
    评估生成结果是否基于文档并正确回答问题
    :param state:当前状态图，包含问题，文档和生成结果
    :return:下个节点的名称
    """

    log.info('---检查产生内容是否存在幻觉---')
    question = state['question']
    documents = state['documents']
    generation = state['generation']

    score = hallucination_grader_chain.invoke({"generation": generation, "documents": documents})
    grade = score.binary_score

    if grade == 'yes':
        log.info('---判定：生成内容基于参考文档---')
        log.info('---评估：生成回答与问题的匹配度---')
        score = answer_grader_chain.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == 'yes':
            log.info('---判定：生成内容准确回答问题---')
            return 'useful'
        else:
            log.info('---判定：生成内容与问题无关---')
            return 'not useful'
    else:
        log.info('---判定：生成内容与文档无关, 将重新尝试---')
        return 'not supported'


workflow = StateGraph(GraphState)

workflow.add_node('websearch', web_search)
workflow.add_node('retriever', retrieve)
workflow.add_node('generate', generate)
workflow.add_node('grade_documents', grade_documents)
workflow.add_node('transform_query', transform_query)

# 起始路由条件判断
workflow.add_conditional_edges(
    START,
    route_question,
    {
        'websearch': 'websearch',
        'vectorstore': 'retriever'
    }
)

workflow.add_edge('websearch', 'generate')
workflow.add_edge('retriever', 'grade_documents')

# 文档评估后的条件分支
workflow.add_conditional_edges(
    'grade_documents',
    decide_to_generate,
    {
        'websearch': 'websearch',
        'generate': 'generate',
        'transform_query': 'transform_query'
    }
)


workflow.add_conditional_edges(
    'generate',
    grade_generation_v_documents_and_question,
    {
        'useful': END,
        'not useful': 'transform_query',
        'not supported': 'generate'
    }
)

workflow.add_edge('transform_query', 'retriever')

graph = workflow.compile()

draw_graph(graph, "graph_rag2.png")

_printed = set()

if __name__ == '__main__':
    while True:
        question = input('用户：')
        if question.lower() in ['q', 'exit', 'quit']:
            log.info('对话结束，拜拜')
            break
        else:
            inputs = {
                'question': question
            }
            for output in graph.stream(inputs):
                for key, value in output.items():
                    pprint(f'Node "{key}":')
                pprint("\n---\n")

            pprint(value['generation'])