from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

from llm_model.all_llm import openai_llm


class GradeAnswer(BaseModel):
    """评估回答是否解决用户问题的二元评分模型"""
    binary_score: str = Field(description='回答是否解决了问题,取值为"yes"或"no"')

structured_llm_grader = openai_llm.with_structured_output(GradeAnswer)

system = """您是一个评估回答是否解决用户问题的评分器。 \n
给出 'yes' 或 'no' 的二元评分。'yes' 表示回答确实解决了该问题。
"""

answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "用户问题: \n\n {question} \n\n 生成回答: \n\n {generation}"),
    ]
)

answer_grader_chain = answer_prompt | structured_llm_grader

