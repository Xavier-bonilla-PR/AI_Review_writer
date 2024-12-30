#Refactored code. Does it work the same?
#I think i can now change the models once for all files?
#Still need to implement more modularity and pdf check if already in the folder

import os
import json
import time
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import all necessary classes (commented out imports are assumed to be needed)
from PDF_getter import SciHubPMCPubMedCrawler
from article_labeler import ArticleLabel
from article_summarizer import ArticleSummary
from outline_maker import OutlineMaker
from ref_remover import list_files, RefRemove
from outline_refiner import OutlineProcessor
from RAG_txt_uploader import TxtUpload
from RAG_query import RagQuery
from RAG_summarizer import RagSummary
from section_split import SectionSplit
from saving_point import SavePoint
from outline_split import OutlineSplit
from essay_writer import EssayWriter
from pdf_maker import EssayBuilder

def crawl_pdfs(iteration_number):
    download_folder = f"pmc_pdfs_{iteration_number}"
    crawler = SciHubPMCPubMedCrawler(download_folder=download_folder)
    article_id = input("Enter the PMC ID or PubMed ID to crawl: ").strip()
    results = crawler.crawl_references(article_id)

    if results:
        # First pass summary
        print("\nFirst pass summary:")
        for i, ref in enumerate(results, 1):
            print(f"{i}. {ref['text'][:100]}...")
            if ref['doi']:
                print(f"   DOI: {ref['doi']}")
            if 'pdf' in ref:
                print(f"   PDF: {ref['pdf']}")
            elif 'pdf_error' in ref:
                print(f"   PDF Error: {ref['pdf_error']}")

        # Second pass for missing PDFs
        results = crawler.second_pass_for_missing_pdfs(results, article_id)

        # Final summary
        print("\nFinal summary after second pass:")
        for i, ref in enumerate(results, 1):
            print(f"{i}. {ref['text'][:100]}...")
            if ref['doi']:
                print(f"   DOI: {ref['doi']}")
            if 'pdf' in ref:
                print(f"   PDF: {ref['pdf']}")
            elif 'pdf_error' in ref:
                print(f"   PDF Error: {ref['pdf_error']}")
    else:
        print("Failed to retrieve or extract data from the article.")

    return results

def setup_environment():
    load_dotenv()
    openai_api_key = os.environ.get("AI_KEY")
    os.environ['OPENAI_API_KEY'] = os.getenv("AI_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", max_tokens=4096)
    return openai_api_key, model

def label_and_summarize_articles(iteration_number):
    labeler = ArticleLabel(f'pmc_pdfs_{iteration_number}')
    results = labeler.review_pdfs()
    with open(f'data_labels_{iteration_number}.txt', 'w') as file:
        json.dump(results, file, indent=4)
    
    analyzer = ArticleSummary(f"data_labels_{iteration_number}.txt", f"data_summary_full_{iteration_number}.txt", f"pmc_pdfs_{iteration_number}")
    analyzer.run()

def create_outline(iteration_number, topic):
    outline_maker = OutlineMaker(f"data_summary_full_{iteration_number}.txt", f"data_comm_{iteration_number}.txt", f"combined_outline_{iteration_number}.txt")
    outline_maker.setup_api_key()
    outline_maker.load_data(chunk_size=10)
    outline_maker.focused_outlines(topic)
    outline_maker.combining_outline(topic)

def refine_outline(openai_api_key, iteration_number):
    processor = OutlineProcessor(openai_api_key)
    processor.process_outline(f'combined_outline_{iteration_number}.txt', f'data_summary_full_{iteration_number}.txt', f'outline_refined_{iteration_number}.txt')

def remove_references(iteration_number):
    reflitname = list_files(f'pmc_pdfs_{iteration_number}')
    output_folder = f'data_{iteration_number}'
    os.makedirs(output_folder, exist_ok=True)
    
    for item in reflitname:
        pdf_path = f'pmc_pdfs_{iteration_number}/{item}'
        output_path = f'{output_folder}/{item[:-4]}_noref.txt'
        converter = RefRemove(pdf_path, output_path)
        converter.pdf_to_txt()

def upload_to_vector_database():
    processor = TxtUpload()
    documents = processor.load_documents()
    chunks = processor.split_documents(documents)
    chunks_all = processor.split_into_chunks(chunks)
    for items in chunks_all:
        processor.add_to_chroma(items)

def rag_loop(iteration_number, openai_api_key):
    with open(f'outline_refined_{iteration_number}.txt', 'r', encoding='utf-8') as file:
        outline = file.read()
    
    sec_split = SectionSplit(f'save_data_file_{iteration_number}.json')
    outline_sections = sec_split.parse_outline(outline)
    
    svpnt = SavePoint(f'save_file_{iteration_number}.json', f'save_data_file_{iteration_number}.json')
    checkpoint = svpnt.load_checkpoint()
    if checkpoint:
        outline_sections = checkpoint
    
    qr = RagQuery(openai_api_key)
    sr = RagSummary()
    
    for t, item in enumerate(outline_sections, 1):
        update_list = outline_sections[t:]
        RAG_response_all = []
        x = len(outline_sections)
        print(f"Going for item #{t}/{x}")
        response = qr.query_rag(item)
        summed1 = sr.summarizing_outline(response)
        summed2 = sr.add_more_details(response, summed1)
        RAG_response_all.append(response)
        time.sleep(0.8)
        
        for _ in range(2):
            response_loop = qr.query_rag(summed2)
            RAG_response_all.append(response_loop)
            summed1_loop = sr.summarizing_outline(RAG_response_all)
            summed2 = sr.add_more_details(RAG_response_all, summed1_loop)
            time.sleep(0.8)

        svpnt.save_data(item, summed2)
        svpnt.save_checkpoint(update_list)
        
    
    improved_outline = sec_split.replace_bullet_points(outline)
    with open(f'outline_improved_{iteration_number}.txt', 'w', encoding='utf-8') as file:
        file.write(str(improved_outline))

def write_essay(iteration_number, model, topic):
    essy_wrtr = EssayWriter(model)
    out_split = OutlineSplit()
    pdf_dict = {"subtitle": [], "subsubtitle": [], "parragraph": []}
    
    file_path = f'outline_improved_{iteration_number}.txt'
    outline_list = out_split.process_text_file(file_path)
    
    for i, section in enumerate(outline_list):
        roman_title = section[2]
        pdf_dict["subtitle"].append(roman_title)
        essy_wrtr.add_entry_to_file(f'lit_rev_{iteration_number}.txt', roman_title)
        
        for j, subsection in enumerate(section[1]):
            subtitle = subsection[2]
            pdf_dict["subsubtitle"].append(subtitle)
            
            item = str(subsection[1])
            detailed_sentence = essy_wrtr.write_section(item)
            pdf_dict["parragraph"].append(detailed_sentence)
            
            essy_wrtr.add_entry_to_file(f'lit_rev_{iteration_number}.txt', subtitle)
            essy_wrtr.add_entry_to_file(f'lit_rev_{iteration_number}.txt', detailed_sentence)
            time.sleep(1)
    
    with open(f'lit_rev_{iteration_number}.txt', 'r', encoding='utf-8') as file:
        lit_rev = file.read()
    
    abstract = essy_wrtr.writing_abstract(lit_rev, topic)
    pdf_dict["abstract"] = abstract
    title = essy_wrtr.writing_title(abstract)
    pdf_dict["title"] = title
    
    essy_wrtr.add_entry_to_json(f'lit_full_rev_{iteration_number}.json', pdf_dict)
    essy_wrtr.add_entry_to_file(f'lit_full_rev_{iteration_number}.txt', "Abstract")
    essy_wrtr.add_entry_to_file(f'lit_full_rev_{iteration_number}.txt', abstract)
    essy_wrtr.add_entry_to_file(f'lit_full_rev_{iteration_number}.txt', lit_rev)
    
    return pdf_dict

def create_pdf(iteration_number, pdf_dict, outline_list):
    builder = EssayBuilder(f'Literature_review_{iteration_number}.pdf')
    builder.add_title(pdf_dict["title"])
    builder.add_subtitle("Abstract")
    builder.add_paragraph(pdf_dict["abstract"])
    
    t = 0
    for i, section in enumerate(outline_list):
        builder.add_subtitle(pdf_dict["subtitle"][i])
        num_subsubtitles = len(section[1])
        
        for j in range(num_subsubtitles):
            if t < len(pdf_dict["subsubtitle"]) and t < len(pdf_dict["parragraph"]):
                builder.add_sub_subtitle(pdf_dict["subsubtitle"][t])
                builder.add_paragraph(pdf_dict["parragraph"][t])
                t += 1
            else:
                print(f"Warning: Ran out of subsubtitles or paragraphs at index {t}")
                break
    
    builder.build()
    print(f"PDF saved as Literature_review_{iteration_number}.pdf")

def main():
    iteration_number = input("Iteration #? ")
    openai_api_key, model = setup_environment()
    
    label_and_summarize_articles(iteration_number)
    
    topic = 'Evaluation of all the modeling and computational simulation efforts to address the different aspects of CAR T-cell therapy'
    create_outline(iteration_number, topic)
    
    refine_outline(openai_api_key, iteration_number)
    
    remove_references(iteration_number)
    
    upload_to_vector_database()
    
    rag_loop(iteration_number, openai_api_key)
    
    pdf_dict = write_essay(iteration_number, model, topic)
    
    out_split = OutlineSplit()
    outline_list = out_split.process_text_file(f'outline_improved_{iteration_number}.txt')
    
    create_pdf(iteration_number, pdf_dict, outline_list)

if __name__ == "__main__":
    main()