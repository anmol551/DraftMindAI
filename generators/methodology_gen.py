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

    # 1. Generate TOC
    template_toc = gen.load_prompt("methodology_toc.txt")
    prompt_toc = template_toc.format(
        pp=gen.prompt_parameters,
        a=pipeline_content,
    )
    print("Generating Methodology TOC...")
    toc_content = gen.generate(prompt_toc)

    # 2. Validate TOC
    template_val = gen.load_prompt("methodology_val.txt")
    prompt_val = template_val.format(
        pp=gen.prompt_parameters,
        toc=toc_content,
        a=pipeline_content,
        b=gen.web_app_summary
    )
    print("Validating Methodology TOC...")
    validated_toc = gen.generate(prompt_val)
    
    # Save validated TOC for use in implementation chapter
    import os
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/methodology_toc_content.txt", "w", encoding="utf-8") as f:
        f.write(validated_toc)

    # 3. Generate Content (Non-Models)
    template_content_part1 = gen.load_prompt("methodology_content_part1.txt")
    prompt_content_part1 = template_content_part1.format(
        pp=gen.prompt_parameters,
        toc=validated_toc,
        a=pipeline_content,
        b=title_and_citation,
        c=gen.web_app_summary
    )

    print("Generating Methodology Content (Excluding Models)...")
    content_part1 = gen.generate(prompt_content_part1)

    # 4. Generate Content (Models Only)
    template_content_part2 = gen.load_prompt("methodology_content_part2.txt")
    prompt_content_part2 = template_content_part2.format(
        pp=gen.prompt_parameters,
        toc=validated_toc,
        a=pipeline_content,
        b=title_and_citation,
    )

    print("Generating Methodology Content (Models Only)...")
    content_part2 = gen.generate(prompt_content_part2)

    content = content_part1 + "\n\n" + content_part2

    try:
        import unicodedata
        content.encode('utf-8')
    except UnicodeEncodeError:
        prompt_ascii1 = prompt_content_part1.encode('ascii', 'ignore').decode('ascii')
        prompt_ascii2 = prompt_content_part2.encode('ascii', 'ignore').decode('ascii')
        content_part1 = gen.generate(prompt_ascii1)
        content_part2 = gen.generate(prompt_ascii2)
        content = content_part1 + "\n\n" + content_part2

    gen.save("OutputFiles/methodology.txt", {"METHODOLOGY": content}, label="METHODOLOGY")
