from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from llm_model.all_llm import openai_llm


class RouteQuery(BaseModel):
    """将用户查询路由到最相关的数据源"""
    datasource: Literal['vectorstore', 'web_search'] = Field(
        ...,
        description="根据用户问题选择将其路由到向量知识库或网络搜索",
    )

structured_llm_router = openai_llm.with_structured_output(RouteQuery)

system_prompt = """你是一个擅长将用户问题路由到向量知识库或网络搜索的专家。 \n
向量知识库包含与半导体材料，芯片制造，光刻技术相关的文档。 \n
对于这些主题的问题请使用向量数据库，其他情况使用网络搜索。 \n
"""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}")
    ]
)

question_router_chain = route_prompt | structured_llm_router

