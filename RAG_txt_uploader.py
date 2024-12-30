#Takes txt files and embeds them
#Is organized
#untested

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv


class TxtUpload:
    def __init__(self):
        load_dotenv(find_dotenv())
        os.environ["OPENAI_API_KEY"] = os.getenv('AI_KEY')
        self.CHROMA_PATH = 'chroma'
        self.DATA_PATH = 'data'

    @staticmethod
    def split_into_chunks(input_list, chunk_size=166):
        chunks = []
        for i in range(0, len(input_list), chunk_size):
            chunk = input_list[i:i + chunk_size]
            chunks.append(chunk)
        return chunks

    def load_documents(self):
        documents = []
        for filename in os.listdir(self.DATA_PATH):
            if filename.endswith('.txt'):
                file_path = os.path.join(self.DATA_PATH, filename)
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
        return documents

    @staticmethod
    def split_documents(documents: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80,
            length_function=len,
            is_separator_regex=False,
        )
        return text_splitter.split_documents(documents)

    @staticmethod
    def get_embedding_function():
        return OpenAIEmbeddings(model="text-embedding-3-small")

    def add_to_chroma(self, chunks: list[Document]):
        db = Chroma(
            persist_directory=self.CHROMA_PATH, embedding_function=self.get_embedding_function()
        )

        chunks_with_ids = self.calculate_chunk_ids(chunks)

        existing_items = db.get(include=[])
        existing_ids = set(existing_items["ids"])
        print(f"Number of existing documents in DB: {len(existing_ids)}")

        new_chunks = []
        for chunk in chunks_with_ids:
            if chunk.metadata["id"] not in existing_ids:
                new_chunks.append(chunk)

        if len(new_chunks):
            print(f"Adding new documents: {len(new_chunks)}")
            new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
            db.add_documents(new_chunks, ids=new_chunk_ids)
        else:
            print("No new document to add")

    @staticmethod
    def calculate_chunk_ids(chunks):
        last_file_id = None
        current_chunk_index = 0

        for chunk in chunks:
            source = chunk.metadata.get("source")
            current_file_id = source
            if current_file_id == last_file_id:
                current_chunk_index += 1
            else:
                current_chunk_index = 0

            chunk_id = f"{current_file_id}:{current_chunk_index}"
            last_file_id = current_file_id

            chunk.metadata["id"] = chunk_id 
        return chunks
    
def main():
    processor = TxtUpload()
    documents = processor.load_documents()
    chunks = processor.split_documents(documents)
    chunks_all = processor.split_into_chunks(chunks)
    print(type(chunks_all))
    print(type(chunks_all[0]))
    print(type(chunks_all[0][1]))
    print(len(chunks_all))
    for items in chunks_all:
        print(len(items))
        processor.add_to_chroma(items)

if __name__ == "__main__":
    main()