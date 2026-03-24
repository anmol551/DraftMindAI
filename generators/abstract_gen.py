"""
abstract_gen.py — generates the Abstract section.
"""

from generators.base import BaseGenerator
import pandas as pd


def generate_abstract():
    gen = BaseGenerator(chapter_name="ABSTRACT", section_key="ABSTRACT")
    counts = gen.get_counts()

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')
    title_and_citation = paper_citation[['title', 'citation']]

    template = gen.load_prompt("abstract.txt")
    prompt = template.format(
        pp=gen.prompt_parameters,
        wc=counts['MAIN'],
        a=gen.code_summary_val_specific,
        b=gen.web_app_summary,
        c=gen.data_details,
    )

    content = gen.generate(prompt)
    gen.save("OutputFiles/abstract.txt", {"ABSTRACT": content}, label="ABSTRACT")
    return content
