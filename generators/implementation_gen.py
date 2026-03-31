"""
implementation_gen.py — generates the Implementation and Web App Development sections.
"""

from generators.base import BaseGenerator
from generators.methodology_gen import parse_toc_sections, count_content_words
from pathlib import Path
import os
import pandas as pd


def generate_implementation_toc():
    gen = BaseGenerator(chapter_name="IMPLEMENTATION", section_key="IMPLEMENTATION")

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

    # ── 1. Generate TOC ────────────────────────────────────────────────────────
    template_toc = gen.load_prompt("implementation_toc.txt")
    prompt_toc = template_toc.format(
        pp=gen.prompt_parameters,
        pipeline=pipeline_content,
        methodology_toc=methodology_toc_content,
        a=gen.code_summary_val_specific,
        b=gen.web_app_summary
    )
    print("Generating Implementation TOC...")
    implementation_toc = gen.generate(prompt_toc)

    # Save TOC for downstream use
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/implementation_toc_content.txt", "w", encoding="utf-8") as f:
        f.write(implementation_toc)
    

    with open("InputFiles/implementation_toc_content.txt", "r", encoding="utf-8") as f:
        implementation_toc = f.read()
        
    return implementation_toc

def generate_implementation_content(implementation_toc: str):
    gen = BaseGenerator(chapter_name="IMPLEMENTATION", section_key="IMPLEMENTATION")

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')
    title_and_citation = paper_citation[['title', 'citation']]

    # Load pipeline
    pipeline_path = gen.config.get('PIPELINE', 'InputFiles/pipeline.txt')
    try:
        pipeline_content = Path(pipeline_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        pipeline_content = ""
        print(f"Warning: Pipeline file not found at '{pipeline_path}'.")

    # Save the human-validated TOC to disk
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/implementation_toc_content.txt", "w", encoding="utf-8") as f:
        f.write(implementation_toc)

    # ── 2. Generate Content — one LLM call per section ────────────────────────
    sections = parse_toc_sections(implementation_toc)

    template_section = gen.load_prompt("implementation_content_section.txt")
    template_expand  = gen.load_prompt("implementation_content_expand.txt")

    print("Generating Implementation Content (section by section)...")
    section_outputs = []

    for section in sections:
        print(f"  → Writing: {section['title']} [{section['words']} words]...")
        prompt = template_section.format(
            pp=gen.prompt_parameters,
            section=section['block'],
            words=section['words'],
            code_summary=gen.code_summary_val_specific,
            pipeline=pipeline_content,
        )
        output = gen.generate(prompt)

        # Word count guard — expand if below 85% of target, retry up to 2 times
        target_words = section['words']
        for attempt in range(2):
            current_words = count_content_words(output)
            if current_words >= target_words * 0.85:
                break
            gap = target_words - current_words
            print(f"     ⚠ Short by ~{gap} words ({current_words}/{target_words}), expanding (attempt {attempt+1})...")
            expand_prompt = template_expand.format(
                pp=gen.prompt_parameters,
                section=section['block'],
                content=output,
                words=target_words,
                current_words=current_words,
                gap=gap,
                pipeline=pipeline_content,
            )
            output = gen.generate(expand_prompt)
            print(f"     ✓ Expanded to ~{count_content_words(output)} words")

        section_outputs.append(output)

    implementation_content = "\n\n".join(section_outputs)

    # ── 3. Save ───────────────────────────────────────────────────────────────
    os.makedirs("OutputFiles", exist_ok=True)
    with open("OutputFiles/implementation.txt", "w", encoding="utf-8") as f:
        f.write(implementation_content)