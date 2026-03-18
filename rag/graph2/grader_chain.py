from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_model.all_llm import openai_llm


class GradeDocuments(BaseModel):
    """对检索到的文档进行相关性评分的二元判断"""
    binary_score: str = Field(description='相关性评分"yes"或"no"')

structured_llm_grader = openai_llm.with_structured_output(GradeDocuments)

system_prompt = """你是一个评估检索文档与用户问题相关性的评分器。 \n
    如果文档包含与用户问题相关的关键词或语义含义，则评为相关。 \n
    不需要非常严格的测试，目前是过滤掉错误的检索结果。 \n
    给出 'yes' 或 'no' 的二元评分来表示文档是否与问题相关。
"""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
    ]
)

retriever_grader_chain = grade_prompt | structured_llm_grader