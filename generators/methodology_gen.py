"""
methodology_gen.py — generates the Methodology section.
"""

from generators.base import BaseGenerator
from pathlib import Path
import pandas as pd
import re, os


def count_content_words(text: str) -> int:
    """Count words in content, ignoring [FIGURE:...] and [CAPTION:...] placeholder lines."""
    lines = text.splitlines()
    filtered = [
        line for line in lines
        if not re.match(r'\s*\[(FIGURE|CAPTION):', line, re.IGNORECASE)
    ]
    return len(' '.join(filtered).split())


def parse_toc_sections(toc: str) -> list:
    """
    Parse a TOC string into a list of section dicts.
    Each dict has:
      - 'block'  : the full text block for this section (heading + subheadings)
      - 'title'  : heading title (without number or word count)
      - 'words'  : integer target word count (or 200 if not found)
      - 'is_model': True if this is the Models section
    """
    sections = []
    current_lines = []

    for line in toc.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # A top-level heading matches e.g. "3.1 Research Design [250 words]"
        if re.match(r'^\d+\.\d+\s+\S', stripped) and not re.match(r'^\d+\.\d+\.\d+', stripped):
            if current_lines:
                sections.append(_build_section(current_lines))
            current_lines = [stripped]
        else:
            current_lines.append(stripped)

    if current_lines:
        sections.append(_build_section(current_lines))

    return sections


def _build_section(lines: list) -> dict:
    heading_line = lines[0]
    # Extract word count from e.g. "[250 words]" or "[250]"
    match = re.search(r'\[(\d+)(?:\s*words?)?\]', heading_line, re.IGNORECASE)
    words = int(match.group(1)) if match else 200
    # Extract title  (strip number and word count bracket)
    title = re.sub(r'^\d+\.\d+\s+', '', heading_line)
    title = re.sub(r'\[\d+(?:\s*words?)?\]', '', title, flags=re.IGNORECASE).strip()
    block = '\n'.join(lines)
    is_model = bool(re.search(r'\bmodel[s]?\b', title, re.IGNORECASE))
    return {'block': block, 'title': title, 'words': words, 'is_model': is_model}


def generate_methodology_toc():
    gen = BaseGenerator(chapter_name="METHODOLOGY", section_key="METHODOLOGY")

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
        
    return validated_toc

def generate_methodology_content(validated_toc: str):
    gen = BaseGenerator(chapter_name="METHODOLOGY", section_key="METHODOLOGY")

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')
    title_and_citation = paper_citation[['title', 'citation']]

    # Load pipeline
    pipeline_path = gen.config.get('PIPELINE', 'InputFiles/pipeline.txt')
    try:
        pipeline_content = Path(pipeline_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        pipeline_content = ""
        print(f"Warning: Pipeline file not found at '{pipeline_path}'.")

    # Save the human-validated TOC to disk so downstream chapters access the correct edited version
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/methodology_toc_content.txt", "w", encoding="utf-8") as f:
        f.write(validated_toc)

    # 3. Generate Content (Non-Models) — one LLM call per section
    template_content_part1 = gen.load_prompt("methodology_content_part1.txt")
    sections = parse_toc_sections(validated_toc)
    non_model_sections = [s for s in sections if not s['is_model']]
    model_sections = [s for s in sections if s['is_model']]

    print("Generating Methodology Content (Excluding Models)...")
    section_outputs = []
    template_expand = gen.load_prompt("methodology_content_expand.txt")
    for section in non_model_sections:
        print(f"  → Writing: {section['title']} [{section['words']} words]...")
        prompt = template_content_part1.format(
            pp=gen.prompt_parameters,
            section=section['block'],
            words=section['words'],
            a=pipeline_content,
            c=gen.web_app_summary,
        )
        output = gen.generate(prompt)

        # Word count check — expand if significantly short (threshold: 85%), retry up to 2 times
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
                a=pipeline_content,
            )
            output = gen.generate(expand_prompt)
            print(f"     ✓ Expanded to ~{count_content_words(output)} words")

        section_outputs.append(output)


    content_part1 = "\n\n".join(section_outputs)

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

    # Word count check for Models section — expand if significantly short (threshold: 85%), retry up to 2 times
    models_target_words = sum(s['words'] for s in model_sections) if model_sections else 200
    template_expand = gen.load_prompt("methodology_content_expand.txt")
    for attempt in range(2):
        current_words = count_content_words(content_part2)
        if current_words >= models_target_words * 0.85:
            break
        gap = models_target_words - current_words
        print(f"     ⚠ Models short by ~{gap} words ({current_words}/{models_target_words}), expanding (attempt {attempt+1})...")
        expand_prompt = template_expand.format(
            pp=gen.prompt_parameters,
            section=validated_toc,
            content=content_part2,
            words=models_target_words,
            current_words=current_words,
            gap=gap,
            a=pipeline_content,
        )
        content_part2 = gen.generate(expand_prompt)
        print(f"     ✓ Models expanded to ~{count_content_words(content_part2)} words")

    content = content_part1 + "\n\n" + content_part2

    gen.save("OutputFiles/methodology.txt", {"METHODOLOGY": content}, label="METHODOLOGY")


