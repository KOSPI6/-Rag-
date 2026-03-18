from typing import List

from langchain_core.documents import Document
from langchain_milvus import Milvus, BM25BuiltInFunction
from pymilvus import IndexType, MilvusClient, Function
from pymilvus.client.types import MetricType, DataType, FunctionType

from document.markdown_parser import MarkdownParser
from llm_model.embeddings_model import qwen_embedding
from utils.load_env import MILVUS_URI, COLLECTION_NAME


class MilvusVectorSave:
    """把新的document数据插入到数据库中"""

    def __init__(self):
        """自定义collection的索引"""
        self.vector_store_saved: Milvus = None


    def create_connection(self):
        client = MilvusClient(uri=MILVUS_URI)
        schema = client.create_schema()

        schema.add_field(field_name='id', datatype=DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field(field_name='text', datatype=DataType.VARCHAR, max_length=6000, enable_analyzer=True,
                         analyzer_params={"tokenizer": "jieba", "filter": ["cnalphanumonly"]})  # analyzer_params={"type": "chinese"}
        schema.add_field(field_name='category', datatype=DataType.VARCHAR, max_length=1000)
        schema.add_field(field_name='source', datatype=DataType.VARCHAR, max_length=1000)
        schema.add_field(field_name='filename', datatype=DataType.VARCHAR, max_length=1000, nullable=True)
        schema.add_field(field_name='filetype', datatype=DataType.VARCHAR, max_length=1000, nullable=True)
        schema.add_field(field_name='title', datatype=DataType.VARCHAR, max_length=1000, default_value="Untitled")
        schema.add_field(field_name='category_depth', datatype=DataType.INT64, nullable=True)
        schema.add_field(field_name='sparse', datatype=DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field(field_name='dense', datatype=DataType.FLOAT_VECTOR, dim=1024)

        bm25_function = Function(
            name='text_bm25_emb',
            input_field_names=['text'],
            output_field_names=['sparse'],
            function_type=FunctionType.BM25,
        )

        schema.add_function(bm25_function)
        index_params = client.prepare_index_params()

        index_params.add_index(
            field_name='sparse',
            index_name='sparse_inverted_index',
            index_type='SPARSE_INVERTED_INDEX',
            metric_type='BM25',
            params={
                'inverted_index_algo': 'DAAT_MAXSCORE',
                'bm25_k1': 1.6,
                'bm25_b': 0.75
            },
        )

        index_params.add_index(
            field_name='dense',
            index_name='dense_vector_index',
            index_type='HNSW',
            metric_type=MetricType.IP,
            params={'M': 16, 'efConstruction': 64}
        )

        if COLLECTION_NAME in client.list_collections():
            client.release_collection(collection_name=COLLECTION_NAME)
            client.drop_index(collection_name=COLLECTION_NAME, index_name='sparse_inverted_index')
            client.drop_collection(collection_name=COLLECTION_NAME)

        client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema,
            index_params=index_params,
        )

    def create_collection(self, is_first=True):
        """创建一个collection: milvus + langchain"""
        self.vector_store_saved = Milvus(
            embedding_function=qwen_embedding,
            collection_name=COLLECTION_NAME,
            builtin_function=BM25BuiltInFunction(),
            vector_field=['dense', 'sparse'],
            consistency_level='Strong',
            auto_id=True,
            connection_args={'uri': MILVUS_URI}
        )

    def add_document(self, data: List[Document]):
        """把新的document保存到milvus中"""
        self.vector_store_saved.add_documents(documents=data)


if __name__ == '__main__':
    file_path = r'C:\Users\35718\PycharmProjects\Rag_Project\datas\md\tech_report_0tfhhamx.md'
    parser = MarkdownParser()
    docs = parser.parse_markdown_to_documents(md_file=file_path)
    mv = MilvusVectorSave()
    mv.create_connection()
    mv.create_collection()
    mv.add_document(docs)

    client = mv.vector_store_saved.client
    #得到表结构
    desc_collection = client.describe_collection(
        collection_name=COLLECTION_NAME
    )
    print(f'表结构是：{desc_collection}')

    #得到当前表的所有的index
    res = client.list_indexes(collection_name=COLLECTION_NAME)
    print(f'表中的所有索引：{res}')

    if res:
        for i in res:
            #得到索引描述
            desc_index = client.describe_index(
                collection_name=COLLECTION_NAME,
                index_name=i
            )
            print(f'索引描述：{desc_index}')


    result = client.query(
        collection_name=COLLECTION_NAME,
        filter="category == 'Title'", #查询category=='Title'的文档
        output_fields=['text','category','filename']   #指定返回的字段
    )

    print(f'测试过滤查询的结果是：{result}')
