from typing import List

from langchain_core.documents import Document
from langgraph.graph import MessagesState


class GraphState(MessagesState):
    """
    表示图处理流程的状态信息

    属性说明：
        question: 用户提出的问题文本
        transform_count: 转换查询的次数
        generation: 语言模型生成的回答文本
        document: 检索到的相关文档列表
    """

    question: str # 储存当前处理的用户问题
    transform_count: int # 存储转换查询的次数
    generation: str # 储存LLM生成的回答内容
    documents: List[Document] # 储存检索到的相关文档
