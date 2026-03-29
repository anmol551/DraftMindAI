"""
result_gen.py — generates Results + Conclusion + Future Work.

Cycle 1: Full Results chapter (5.1–5.8) in a single generation call.
Cycle 2: Conclusion + Future Work in a single generation call.
"""

from generators.base import BaseGenerator
from pathlib import Path
import re
import os
import pandas as pd


# ── helpers ───────────────────────────────────────────────────────────────────

FIGURE_RULE = """

FIGURE PLACEHOLDERS RULE (Apply to ALL sections that discuss plots, charts, or visual outputs):
Must start from new line
Every plot, chart, graph, or screenshot MUST have a placeholder using
this exact 3-block structure placed INLINE immediately after the sentence
that describes the figure:

[Figure 5.X: short caption]
Caption: Figure 5.X — full caption sentence
Description: one paragraph of 60-80 words explaining what the figure
          reveals, key values, patterns, and conclusions

X increments globally across the entire results section.
Never reset between subsections. Use ONLY [Figure 5.X: caption] format.
"""

COMMON_GUIDELINES = """
Important Guidelines:
    1. Use UK English.
    2. Do not use asterisk (*).
    3. Use commas only when necessary.
    4. Write in very simple and clear language suitable for a student thesis.
       Maintain a reflective tone so the content reads like a natural explanation.
    5. Do not use any of the following words: leverage, rigor, overall, additionally,
       furthermore, moreover, nuanced, notably, utilised, foster, pivot, pivotal.
    6. Strictly do not use parentheses for mentioning metric values — write them
       inline in the sentence.
    7. For metrics ranging from 0 to 1, convert them to percentage format using the
       % symbol, up to 2 decimal places.
    8. Do NOT output any Markdown heading symbols (#, ##, ###, etc.). Write all headings as plain text.
"""


# ── prompt builders ───────────────────────────────────────────────────────────

def _results_prompt(gen, fmt, counts):
    """Build the full results chapter prompt (sections 5.1–5.8)."""
    base_paper_citation = gen.config['BASE_PAPER_CITATION']

    template = gen.load_prompt(f"result/performance_format_{fmt}.txt")

    body = template.format(
        figure_rule=FIGURE_RULE,
        common=COMMON_GUIDELINES,
        wc_intro=counts.get('INTRO', 50),
        wc_table_explain=counts.get('TABLE_EXPLAIN', 100),
        wc_per_model=counts.get('PER_MODEL', 200),
        wc_per_chart_type=counts.get('PER_CHART_TYPE', 200),
        wc_comparison=counts.get('COMPARISON', 300),
        wc_webapp=counts.get('WEBAPP', 100),
        wc_webapp_screenshots=counts.get('WEBAPP_SCREENSHOTS', 'N'),
        wc_benchmark=counts.get('BENCHMARK', 100),
        wc_novelty=counts.get('NOVELTY', 200),
        wc_sig_obj=counts.get('SIG_OBJECTIVES', 200),
        wc_sig_limit=counts.get('SIG_LIMITATIONS', 100),
        code_summary_val_specific=gen.code_summary_val_specific.split('"model_results":')[-1] if '"model_results":' in gen.code_summary_val_specific else gen.code_summary_val_specific,
        result_summary=gen.result_summary,
        result_plot_title_and_category="{result_plot_title_and_category}",
        base_paper_summary=gen.base_paper_summary,
        base_paper_citation=base_paper_citation,
        web_app_development=gen.web_app_development,
        web_app_testing_results=gen.web_app_testing_results,
        novelty=gen.novelty,
        research_objectives=gen.research_question_and_objectives,
    )
    return gen.prompt_parameters + body


def _conclusion_prompt(gen, counts):
    """Build the conclusion prompt."""
    template = gen.load_prompt("result/conclusion.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('CONCLUSION', 300),
        code_summary=gen.code_summary,
        novelty=gen.novelty,
    )


def _future_work_prompt(gen, counts):
    """Build the future work prompt."""
    template = gen.load_prompt("result/future_work.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('FUTURE_WORK', 300),
        code_summary_val_specific=gen.code_summary_val_specific,
    )


# ── main entry point ──────────────────────────────────────────────────────────

def generate_result_conclusion():
    gen = BaseGenerator(chapter_name="RESULTS", section_key="RESULTS")
    counts = gen.get_counts()
    fmt = gen.format

    # ══════════════════════════════════════════════════════════════════════════
    # CYCLE 1: Full Results Chapter (5.1–5.8)
    # ══════════════════════════════════════════════════════════════════════════

    # Step 1: Collect plot titles
    title_prompt = gen.prompt_parameters + f"""
From the result plot summary, collect all plot titles.
Use Results Summary from:
{gen.result_summary}
"""
    print("Collecting plot titles...")
    result_plot_title_and_category = gen.generate(title_prompt)

    # Step 2: Generate full results chapter
    results_prompt = _results_prompt(gen, fmt, counts)
    # Inject the collected plot titles
    results_prompt = results_prompt.replace(
        "{result_plot_title_and_category}", result_plot_title_and_category
    )

    print("Generating Results chapter...")
    results_content = gen.generate(results_prompt)

    gen.save(
        "OutputFiles/results.txt",
        {"RESULTS": results_content},
        label="RESULTS"
    )

    # # ══════════════════════════════════════════════════════════════════════════
    # # CYCLE 2: Conclusion + Future Work
    # # ══════════════════════════════════════════════════════════════════════════

    # print("Generating Conclusion...")
    # conclusion = gen.generate(_conclusion_prompt(gen, counts))

    # print("Generating Future Work...")
    # future_work = gen.generate(_future_work_prompt(gen, counts))

    # gen.save(
    #     "OutputFiles/conclusion.txt",
    #     {"CONCLUSION": conclusion, "FUTURE WORK": future_work},
    #     label="CONCLUSION AND FUTURE WORK"
    # )
