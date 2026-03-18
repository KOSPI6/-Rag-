from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_model.all_llm import openai_llm


class GradeHallucinations(BaseModel):
    """对生成回答中是否产生幻觉进行二元评分"""

    binary_score: str = Field(description='回答是否基于事实,取值为"yes"或"no"')


structured_llm_grader = openai_llm.with_structured_output(GradeHallucinations)

system = """你是一个对生成回答中是否产生幻觉进行二元评分的评分器。 \n
    如果回答基于/支持给定的事实集，则评为非幻觉，评价为 'yes' 。 \n
    给出 'yes' 或 'no' 的二元评分来表示回答是否产生幻觉。
"""

hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "事实集: \n\n {documents} \n\n 生成内容：{generation}"),
    ]
)

hallucination_grader_chain = hallucination_prompt | structured_llm_grader
