"""
implementation_gen.py — generates the Implementation and Web App Development sections.
"""

from generators.base import BaseGenerator
from pathlib import Path
import os
import pandas as pd


def generate_implementation():
    gen = BaseGenerator(chapter_name="IMPLEMENTATION", section_key="IMPLEMENTATION")
    counts = gen.get_counts()

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')
    title_and_citation = paper_citation[['title', 'citation']]

    # Load pipeline
    pipeline_path = gen.config.get('PIPELINE', 'InputFiles/pipeline.txt')
    methodology_toc_path = gen.config.get('METHODOLOGY_TOC', 'InputFiles/methodology_toc_content.txt')
    try:
        pipeline_content = Path(pipeline_path).read_text(encoding='utf-8')
        methodology_toc_content = Path(methodology_toc_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        pipeline_content = ""
        methodology_toc_content = ""
        print(f"Warning: Pipeline file not found at '{pipeline_path}'.")
        print(f"Warning: Methodology TOC file not found at '{methodology_toc_path}'.")

    # ── Main Implementation section ────────────────────────────────────────
    template = gen.load_prompt("implementation_toc.txt")
    prompt = template.format(
        pp=gen.prompt_parameters,
        pipeline=pipeline_content,
        methodology_toc=methodology_toc_content,
        a=gen.code_summary_val_specific,
        b=gen.web_app_summary
    )
    implementation_toc = gen.generate(prompt)
    
    # Save implementation for use in implementation chapter
    import os
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/implementation_toc_content.txt", "w", encoding="utf-8") as f:
        f.write(implementation_toc)

    # ── Main Implementation section ────────────────────────────────────────
    template = gen.load_prompt("implementation_content.txt")
    prompt = template.format(
        pp=gen.prompt_parameters,
        implementation_toc_content=implementation_toc,
        code_summary_val_specific=gen.code_summary_val_specific,
    )
    implementation_content = gen.generate(prompt)
    
    # save the generated content.
    os.makedirs("OutputFiles", exist_ok=True)
    with open("OutputFiles/implementation.txt", "w", encoding="utf-8") as f:
        f.write(implementation_content)
