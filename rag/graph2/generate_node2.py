from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from graph2.graph_state2 import GraphState
from llm_model.all_llm import deepseek_llm


def generate(state: GraphState):
    """
    生成答案
    :param state:当前的状态
    :return:包含重述问题的更新后的状态
    """
    question = state['question']
    documents = state['documents']

    prompt = PromptTemplate(
        template="你是一个问答任务助手，请根据以下检索到的上下文回答问题。如果不知道答案，请直接说明。回答保持简洁。\n问题：{question} \n上下文：{context} \n",
        input_variables=["question", "context"],
    )

    def format_docs(docs):
        """将多个文档内容合并为一个字符串，用两个换行符分隔每个文档"""
        if isinstance(docs, list):
            return "\n\n".join(doc.page_content for doc in docs)  # 拼接所有文档内容
        else:
            return "\n\n" + docs.page_content

    rag_chain = prompt | deepseek_llm | StrOutputParser()

    # RAG生成过程
    generation = rag_chain.invoke({"context": format_docs(documents), "question": question})  # 调用RAG链生成回答
    return {"documents": documents, "question": question, "generation": generation}  # 返回更新后的状态
