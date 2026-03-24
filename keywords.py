from ai import generate_content
from utils import load_files
import os


def generate_keywords():

    title, literature_review_summary, research_gaps, code_summary, web_app_summary, \
    code_summary_val_specific, novelty, data_details, methodology, \
    research_question_and_objectives, base_paper_summary, result_summary, \
    failed_attempts, web_app_development, web_app_testing_results, \
    prompt_parameters = load_files()

    KEYWORDS_GENERATION_PROMPT = """
    From the code summary provided below, extract the names of:
    - All preprocessing techniques used (e.g. StandardScaler, OneHotEncoder)
    - All machine learning or deep learning models used (e.g. ElasticNet, TabNet)
    - All key layer types used in neural networks (e.g. Conv1D, Dense, Dropout)
    - The web application framework used (e.g. Streamlit)
    - The LLM or API used if any (e.g. GPT-4o-mini)

    Output rules:
    - One name per line, no numbering, no dashes, no bullet points.
    - Do not include evaluation metric names (MAE, R2, Accuracy, etc.).
    - Do not include function names or library import paths.
    - Do not include any explanation or extra text — names only.

    Use the code summary value specific file from:
    {a} {b}

    """.format(a=code_summary_val_specific, b=web_app_summary)

    keywords = generate_content(KEYWORDS_GENERATION_PROMPT)

    os.makedirs("InputFiles", exist_ok=True)

    # Save to a text file
    with open("InputFiles/keywords.txt", "w", encoding="utf-8") as file:
        file.write(keywords)