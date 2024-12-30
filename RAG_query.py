#In CLI put a sentence in "" and it will provide context to an llm from vector database
#untest


import argparse
import os
from dotenv import load_dotenv, find_dotenv
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

class RagQuery:
    CHROMA_PATH = "chroma"
    PROMPT_TEMPLATE = """
    Add to the statement based only on the following context:
    {context}
    ---
    Give specific and concrete and concise details to the statement based on the above context: {statement}
    """

    def __init__(self, open_ai_key):
        self.openai_api_key = open_ai_key
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    @staticmethod
    def get_embedding_function():
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return embeddings

    @staticmethod
    def create_cli():
        parser = argparse.ArgumentParser()
        parser.add_argument("query_text", type=str, help="The query text.")
        args = parser.parse_args()
        return args.query_text

    def query_rag(self, query_text: str):
        # Prepare the DB.
        embedding_function = self.get_embedding_function()
        db = Chroma(persist_directory=self.CHROMA_PATH, embedding_function=embedding_function)

        # Search the DB. 
        results = db.similarity_search_with_score(query_text, k=30)
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        
        prompt_template = ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, statement=query_text)

        # Initialize GPT-4 model
        model = ChatOpenAI(model_name="gpt-4o-mini", api_key=self.openai_api_key)
        
        response = model.invoke(prompt)
        response_text = response.content

        sources = [doc.metadata.get("id", None) for doc, _score in results]
        formatted_response = f"Response: {response_text}\nSources: {sources}"
        print(formatted_response)

        # Saves file
        with open('RAG_context.txt', 'w', encoding='utf-8') as file:
            file.write(context_text)
        
        return response_text

def main():
    rag = RagQuery()
    query_text = RagQuery.create_cli()
    rag.query_rag(query_text)

if __name__ == "__main__":
    main()

    #python RAG_query_pix.py "The therapeutic window for hydrogen sulfide (H2S) donors is severely limited, posing significant challenges for their clinical applications due to the rapid release kinetics of traditional donors like NaHS and Na2S, which leads to an initial surge followed by a swift decline in H2S levels, making it difficult to sustain therapeutic concentrations over extended periods and necessitating frequent dosing or continuous infusion that may not be practical clinically; the narrow therapeutic range with low doses being ineffective and high doses causing toxicity such as respiratory distress and cellular damage; the deterrence of patient compliance and risks to healthcare personnel from the pungent odor; potential adverse interactions with medications like volatile anesthetics; and the introduction of unpredictable biological effects from impurities like sulfate and polysulfides in donor preparations, all of which underscores the pressing need for developing more controlled, synthetic H2S donors with tunable, sustained release kinetics, favorable pharmacokinetic profiles, and the ability to account for variations based on factors such as administration route, chemical structure, and patient characteristics to enhance clinical applicability while optimizing safety and efficacy."