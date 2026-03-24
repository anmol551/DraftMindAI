"""
methodology_gen.py — generates the Methodology section.
"""

from generators.base import BaseGenerator
from pathlib import Path
import pandas as pd


def generate_methodology():
    gen = BaseGenerator(chapter_name="METHODOLOGY", section_key="METHODOLOGY")
    counts = gen.get_counts()

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')
    title_and_citation = paper_citation[['title', 'citation']]

    # Load pipeline
    pipeline_path = gen.config.get('PIPELINE', 'InputFiles/pipeline.txt')
    try:
        pipeline_content = Path(pipeline_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        pipeline_content = ""
        print(f"Warning: Pipeline file not found at '{pipeline_path}'.")

    template = gen.load_prompt("methodology.txt")
    prompt = template.format(
        pp=gen.prompt_parameters,
        # pipeline=pipeline_content,
        # wc_rd=counts['RESEARCH_DESIGN'],
        # wc_dd=counts['DATASET_DESC'],
        # wc_pre=counts['PREPROCESSING'],
        # wc_dyn=counts['DYNAMIC_PRE'],  
        # wc_mod=counts['MODEL_BUILDING'],
        # wc_mod_lay=counts['MODEL_LAYERS'],
        # wc_eval=counts['EVALUATION_METRICS'],
        # wc_llm=counts['LLM_INTEGRATION'],
        # wc_web=counts['WEB_APP_FRAMEWORK'],
        # wc_xai=counts['XAI_FRAMEWORK'],
        # wc_eth=counts['ETHICS'],
        a=pipeline_content,
        b=title_and_citation,
    )

    content = gen.generate(prompt)

    try:
        import unicodedata
        content.encode('utf-8')
    except UnicodeEncodeError:
        prompt_ascii = prompt.encode('ascii', 'ignore').decode('ascii')
        content = gen.generate(prompt_ascii)

    gen.save("OutputFiles/methodology.txt", {"METHODOLOGY": content}, label="METHODOLOGY")
