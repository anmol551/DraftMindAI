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
    try:
        pipeline_content = Path(pipeline_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        pipeline_content = ""
        print(f"Warning: Pipeline file not found at '{pipeline_path}'.")

    # ── Main Implementation section ────────────────────────────────────────
    template = gen.load_prompt("implementation.txt")
    prompt = template.format(
        pp=gen.prompt_parameters,
        pipeline=pipeline_content,
        wc_stat=counts['STATISTICAL_ANALYSIS'],
        wc_eda=counts['EDA'],
        wc_pre=counts['PREPROCESSING'],
        wc_dyn=counts['DYNAMIC_PRE'],
        wc_mod=counts['MODEL_TRAINING'],
        wc_llm=counts['LLM_INTEGRATION'],
        wc_web=counts['WEB_APP_DEVELOPMENT'],
        wc_xai=counts['XAI_IMPLEMENTATION'],
        wc_chal=counts['CHALLENGES'],
        a=gen.code_summary_val_specific,
        b=gen.web_app_summary,
        c=title_and_citation,
    )
    implementation = gen.generate(prompt)

    # ── Web App Development sub-section ────────────────────────────────────
    WAD_PROMPT = gen.prompt_parameters + f"""
Write about web application development in approximately 200 words in the research report.

1. Do not mention the web application framework definition.
2. Keep a single paragraph.
3. Do not mention any definitions.
4. Do not use parentheses to mention values.
5. Do not use function or library names like keras.sequential() etc.
6. Do not mention any code or subheadings.
7. Strictly approximately 200 words.
8. Keep content in past tense.
9. Name the exact framework, UI components, input fields, and
   configurations — do not stay generic.
10. Do not output any Markdown heading symbols.

Note: Implementation only — no theoretical framework.

Use web app summary from:
{gen.web_app_summary}
"""
    web_app_content = gen.generate(WAD_PROMPT)

    # Save web app development to InputFiles for downstream use
    os.makedirs("InputFiles", exist_ok=True)
    with open("InputFiles/wad.txt", "w", encoding='utf-8') as f:
        f.write("Web App Development:\n")
        f.write(web_app_content + "\n\n")

    gen.save(
        "OutputFiles/implementation.txt",
        {"IMPLEMENTATION": implementation},
        label="IMPLEMENTATION"
    )
