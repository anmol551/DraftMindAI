"""
introduction_gen.py — generates the Introduction chapter.

Selects the correct format-specific prompt file from prompts/introduction/,
injects all word counts and data, and generates each section sequentially.
"""

from generators.base import BaseGenerator
from utils import load_question_objectives
import os


# Sections present in each format (determines which prompts to run and labels)
FORMAT_SECTIONS = {
    1: ["BACKGROUND", "PROBLEM STATEMENT", "SIGNIFICANCE", "SCOPE AND LIMITATIONS", "STRUCTURE OF THE REPORT"],
    2: ["BACKGROUND", "PROBLEM STATEMENT", "RESEARCH QUESTION AND OBJECTIVES", "SIGNIFICANCE", "SCOPE AND LIMITATIONS", "RESEARCH GAPS", "STRUCTURE OF THE REPORT"],
    3: ["BACKGROUND", "PROBLEM STATEMENT", "RESEARCH QUESTION AND OBJECTIVES", "SIGNIFICANCE", "SCOPE AND LIMITATIONS", "RESEARCH GAPS", "STRUCTURE OF THE REPORT"],
    4: ["BACKGROUND", "PROBLEM STATEMENT", "RESEARCH QUESTION", "RESEARCH OBJECTIVES", "SIGNIFICANCE", "SCOPE AND LIMITATIONS", "STRUCTURE OF THE REPORT"],
}


def generate_introduction():
    gen = BaseGenerator(chapter_name="INTRODUCTION", section_key="INTRODUCTION")
    counts = gen.get_counts()
    fmt = gen.format

    question, objectives = load_question_objectives()

    # Build common kwargs for format()
    common = dict(
        pp=gen.prompt_parameters,
        wc_bg=counts['BACKGROUND'],
        wc_bg_summ=counts['BACKGROUND_SUMMARY'],
        wc_prob=counts['PROBLEM_STATEMENT'],
        wc_sig=counts['SIGNIFICANCE'],
        wc_scope=counts['SCOPE_LIMITATIONS'],
        wc_struct=counts['STRUCTURE'],
        a=gen.literature_review_summary,
        b=gen.research_gaps,
        c=gen.code_summary_val_specific,
        d=gen.novelty,
        e=gen.web_app_summary,
        f=gen.data_details,
        g=gen.title,
        h=question,
        i=objectives,
    )

    # Formats 2, 3, 4 also have research gaps word counts
    if fmt in (2, 3, 4):
        common['wc_gaps'] = counts.get('GAPS', 130)
        common['wc_gaps_min'] = counts.get('GAPS_MIN', 100)

    # Load the format-specific prompt file
    template = gen.load_prompt(f"introduction/format_{fmt}.txt")

    # Split by section separator and generate each section individually
    sections_raw = template.split("---SECTION_BREAK---")
    section_labels = FORMAT_SECTIONS[fmt]

    generated_sections = {}
    for idx, (section_text, label) in enumerate(zip(sections_raw, section_labels)):
        prompt = section_text.strip().format(**common)
        content = gen.generate(prompt)
        generated_sections[label] = content
        print(f"  ✓ Introduction [{label}] generated")

    gen.save("OutputFiles/introduction.txt", generated_sections, label="INTRODUCTION")
    print("Introduction Generated!")
