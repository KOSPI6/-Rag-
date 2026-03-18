from typing import List

from langchain_experimental.text_splitter import SemanticChunker

from llm_model.embeddings_model import qwen_embedding
from utils.log_utils import log

from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document


class MarkdownParser:
    """
    专门负责markdown文件的解析和切片
    """

    def __init__(self):
        self.text_splitter = SemanticChunker(
            embeddings=qwen_embedding,
            breakpoint_threshold_type='percentile'
        )

    def text_chunker(self, datas: List[Document]) -> List[Document]:
        new_docs = []
        for d in datas:
            if len(d.page_content) > 5000:
                new_docs.extend(self.text_splitter.split_documents([d]))
                continue
            new_docs.append(d)

        return new_docs



    def parse_markdown_to_documents(self, md_file: str, encoding='utf-8')->List[Document]:
        documents = self.parse_markdown(md_file)
        log.info(f"解析文件{md_file}成功，共{len(documents)}个文档")

        merged_documents = self.merge_title_content(documents)
        log.info(f"合并标题和内容成功，共{len(merged_documents)}个文档")

        chunk_documents = self.text_chunker(merged_documents)
        log.info(f"语义切割分块成功，共{len(chunk_documents)}个文档")

        return chunk_documents



    def parse_markdown(self, md_file: str)->List[Document]:
        loader = UnstructuredMarkdownLoader(
            file_path=md_file,
            mode='elements',
            strategy='fast',
        )
        docs=[]
        for doc in loader.lazy_load():
            docs.append(doc)
        return docs

    def merge_title_content(self, datas: List[Document])->List[Document]:
        merged_data=[]
        parent_dict = {}  #是一个字典，包含所有的父document，key为当前父document的ID号
        for document in datas:
            metadata = document.metadata
            if 'languages' in metadata:
                metadata.pop('languages')
            parent_id = metadata.get('parent_id', None)
            category = metadata.get('category', None)
            element_id = metadata.get('element_id', None)

            if category == 'NarrativeText' and parent_id is None:
                merged_data.append(document)
            if category =='Title':
                document.metadata['title'] = document.page_content
                if parent_id in parent_dict:
                    document.page_content = parent_dict[parent_id].page_content + ' -> ' + document.page_content
                parent_dict[element_id] = document
            if category != 'Title' and parent_id is not None:
                parent_dict[parent_id].page_content = parent_dict[parent_id].page_content + ' ' + document.page_content
                parent_dict[parent_id].metadata['category'] = 'content'

        #处理字典
        if parent_dict is not None:
            merged_data.extend(parent_dict.values())

        return merged_data




if __name__ == '__main__':
    file_path = r'C:\Users\35718\PycharmProjects\Rag_Project\datas\md\tech_report_0tfhhamx.md'
    parser = MarkdownParser()
    docs = parser.parse_markdown_to_documents(md_file=file_path)
    for d in docs:
        print(f"元数据：{d.metadata}")
        print(f"标题：{d.metadata.get('title', None)}")
        print(f"doc内容：{d.page_content}\n")
        print('---' * 50)
