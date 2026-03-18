from langchain_core.tools import create_retriever_tool

from document.milvus_db import MilvusVectorSave

mv = MilvusVectorSave()
mv.create_collection()

retriever = mv.vector_store_saved.as_retriever(
    search_type='similarity',
    search_kwargs={
        'k': 4,
        'score_threshold': 0.1,
        'ranker_type': 'rrf',
        'ranker_params': {'k': 100},
        'filter': {'category': 'content'}
    }
)

retriever_tool = create_retriever_tool(
    retriever=retriever,
    name='rag_retriever',
    description='搜索并返回关于“半导体和芯片”的信息，内容涵盖：半导体和芯片的封装测试，光刻胶等。',
)



