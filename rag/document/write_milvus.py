import multiprocessing
import os.path
from multiprocessing import Queue

from document.markdown_parser import MarkdownParser
from document.milvus_db import MilvusVectorSave
from utils.log_utils import log


# 采用分布式，多进程的方式把海量数据写入Milvus数据库中
def file_parser_process(dir_path: str, output_queue: Queue, batch_size: int = 20):
    """进程1：解析目录下所有的md文件并分批放入队列"""
    log.info(f'解析进程开始扫描目录：{dir_path}')

    md_files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.endswith('.md')
    ]

    if not md_files:
        log.warning(f'警告，目录{dir_path}下没有md文件')
        output_queue.put(None)  #发送终止信号
        return

    parser = MarkdownParser()
    doc_batch = []
    for file_path in md_files:
        try:
            docs = parser.parse_markdown_to_documents(file_path)
            if docs:
                doc_batch.extend(docs)

            #达到批次的大小，则发送到队列中
            if len(doc_batch) >= batch_size:
                output_queue.put(doc_batch.copy())
                doc_batch.clear()  #清空当前缓冲区的所有批次数据

        except Exception as e:
            log.error(f'解析文件{file_path}出错：{str(e)}')
            log.exception(e)

    if doc_batch:
        output_queue.put(doc_batch.copy())
        doc_batch.clear()

    output_queue.put(None)
    log.info(f'解析进程结束，共解析了{len(md_files)}个md文件')


def milvus_writer_process(input_queue: Queue):
    """进程2：从队列中读取，并写入Milvus数据库中"""

    mv = MilvusVectorSave()
    mv.create_collection()
    total_count = 0
    while True:
        try:
            data = input_queue.get()  # 阻塞函数
            if data is None:  # 收到了终止信号
                break
            if isinstance(data, list):
                mv.add_document(data)
                total_count += len(data)
                log.info(f'累计添加了{total_count}个document')
        except Exception as e:
            log.error(f'写入进程出错：{str(e)}')
            log.exception(e)


    log.info(f'写入进程结束，总共写入{total_count}个document')

if __name__ == '__main__':
    md_dir = r'D:\agent_project\rag\datas\md'
    queue_maxsize = 40

    mv = MilvusVectorSave()
    mv.create_connection()

    #创建进程间的通信队列
    docs_queue = Queue(maxsize=queue_maxsize)

    #启动子进程
    parser_proc = multiprocessing.Process(
        target=file_parser_process,
        args=(md_dir, docs_queue)
    )
    writer_proc = multiprocessing.Process(
        target=milvus_writer_process,
        args=(docs_queue,)
    )
    parser_proc.start()
    writer_proc.start()

    #等待子进程结束
    parser_proc.join()
    writer_proc.join()

    log.info('系统提示：所有任务完成')
