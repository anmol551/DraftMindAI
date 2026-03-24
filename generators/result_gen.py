"""
result_gen.py — generates Results + Conclusion + Future Work.

Chains all sub-prompt builders (performance evaluation, web app testing,
significance, failed attempts, novelty, conclusion, future work).
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

X increments globally across the entire implementation section.
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
    9. CRITICAL GLOBAL CONSTRAINT: The total combined word count of the entire Results chapter
       MUST NOT EXCEED 1500 words. Be concise and strictly adhere to the word count limit
       for your specific section.
"""


def _extract_last_figure_num(text: str) -> int:
    matches = re.findall(r'\[Figure 5\.(\d+):', text)
    return max((int(n) for n in matches), default=0)


# ── prompt builders ───────────────────────────────────────────────────────────

def _performance_prompt(gen, fmt, counts, code_summary_val_specific,
                         result_summary, result_plot_title_and_category,
                         base_paper_summary, base_paper_citation):
    shared = f"""
Use Code Summary Value Specific, Result Summary, Result Plot Title and Category,
Base Paper Summary, and Base Paper Citation from:
{code_summary_val_specific} {result_summary} {result_plot_title_and_category}
{base_paper_summary} {base_paper_citation}
"""
    template = gen.load_prompt(f"result/performance_format_{fmt}.txt")

    body = template.format(
        figure_rule=FIGURE_RULE,
        wc_intro=counts.get('INTRO', '30 to 50'),
        wc_vis_learn=counts.get('VISUAL_COMPARISON_LEARNING', '30 to 40'),
        wc_vis_xai=counts.get('VISUAL_COMPARISON_XAI', '80 to 90'),
        wc_vis_grp=counts.get('VISUAL_COMPARISON_GROUPED', '120 to 130'),
        wc_vis_ind=counts.get('VISUAL_COMPARISON_INDIVIDUAL', '50 to 60'),
        wc_vis_other=counts.get('VISUAL_COMPARISON_OTHER', '40 to 50'),
        wc_cmp=counts.get('COMPARATIVE_PLOT', '30 to 40'),
        wc_base=counts.get('COMPARISON_WITH_BASE', 150),
        wc_lim=counts.get('LIMITATIONS', 60),
    )
    return gen.prompt_parameters + body + COMMON_GUIDELINES + shared


def _web_app_testing_prompt(gen, web_app_development, web_app_testing_results,
                             figure_start, counts):
    template = gen.load_prompt("result/web_app_testing.txt")
    return gen.prompt_parameters + f"FIGURE_START: {figure_start} — begin figure numbering from Figure 5.{figure_start}\n\n" + template.format(
        figure_rule=FIGURE_RULE,
        common=COMMON_GUIDELINES,
        wc_intro=counts.get('WEB_APP_TESTING_INTRO', '25 to 35'),
        wc_total=counts.get('WEB_APP_TESTING_TOTAL', 200),
        wc_insight=counts.get('WEB_APP_TESTING_INSIGHT', '30 to 40'),
        web_app_development=web_app_development,
        web_app_testing_results=web_app_testing_results,
    )


def _significance_prompt(gen, performance_evaluation, web_app_testing_results, counts):
    template = gen.load_prompt("result/significance.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc_sub1=counts.get('SIGNIFICANCE_SUB1', 80),
        wc_sub2=counts.get('SIGNIFICANCE_SUB2', 120),
        wc_total=counts.get('SIGNIFICANCE_TOTAL', 200),
        performance_evaluation=performance_evaluation,
        web_app_testing_results=web_app_testing_results,
    )


def _failed_attempts_prompt(gen, failed_attempts, figure_start, counts):
    template = gen.load_prompt("result/failed_attempts.txt")
    return gen.prompt_parameters + f"FIGURE_START: {figure_start} — begin figure numbering from Figure 5.{figure_start}\n\n" + template.format(
        figure_rule=FIGURE_RULE,
        common=COMMON_GUIDELINES,
        wc_intro=counts.get('FAILED_ATTEMPTS_INTRO', '25 to 35'),
        wc_total=counts.get('FAILED_ATTEMPTS_TOTAL', 100),
        wc_insight=counts.get('FAILED_ATTEMPTS_INSIGHT', '30 to 40'),
        failed_attempts=failed_attempts,
    )


def _novelty_prompt(gen, novelty, counts):
    template = gen.load_prompt("result/novelty.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('RESEARCH_NOVELTY', 250),
        novelty=novelty,
    )


def _no_base_paper_prompt(gen, code_summary, result_summary, counts):
    template = gen.load_prompt("result/no_base_paper.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('NO_BASE_PAPER', 250),
        code_summary=code_summary,
        result_summary=result_summary,
    )


def _conclusion_prompt(gen, code_summary, novelty, counts):
    template = gen.load_prompt("result/conclusion.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('CONCLUSION', 300),
        code_summary=code_summary,
        novelty=novelty,
    )


def _future_work_prompt(gen, code_summary_val_specific, counts):
    template = gen.load_prompt("result/future_work.txt")
    return gen.prompt_parameters + template.format(
        common=COMMON_GUIDELINES,
        wc=counts.get('FUTURE_WORK', 300),
        code_summary_val_specific=code_summary_val_specific,
    )


# ── main entry point ──────────────────────────────────────────────────────────

def generate_result_conclusion():
    gen = BaseGenerator(chapter_name="RESULTS", section_key="RESULTS")
    counts = gen.get_counts()
    fmt = gen.format

    base_paper_citation = gen.config['BASE_PAPER_CITATION']

    paper_citation = pd.read_csv(gen.config['PAPER_CITATION'], encoding='utf-8')

    # Step 1: Collect plot titles
    title_prompt = gen.prompt_parameters + f"""
From the result plot summary, collect all plot titles.
Use Results Summary from:
{gen.result_summary}
"""
    result_plot_title_and_category = gen.generate(title_prompt)

    # Step 2: Performance evaluation
    perf_prompt = _performance_prompt(
        gen, fmt, counts,
        gen.code_summary_val_specific, gen.result_summary,
        result_plot_title_and_category, gen.base_paper_summary, base_paper_citation
    )
    
    performance_evaluation = gen.generate(perf_prompt)
    last_fig_perf = _extract_last_figure_num(performance_evaluation)
    print(f"Last figure after performance evaluation: 5.{last_fig_perf}")

    # Step 3: Web app testing
    web_app_test = gen.generate(_web_app_testing_prompt(
        gen, gen.web_app_development, gen.web_app_testing_results,
        figure_start=last_fig_perf + 1, counts=counts
    ))
    last_fig_webapp = _extract_last_figure_num(web_app_test)
    print(f"Last figure after web app testing: 5.{last_fig_webapp}")

    # Step 4: Significance
    significance = gen.generate(_significance_prompt(
        gen, performance_evaluation, gen.web_app_testing_results, counts
    ))

    # Step 5: Failed attempts
    failed_attempts_content = gen.generate(_failed_attempts_prompt(
        gen, gen.failed_attempts, figure_start=last_fig_webapp + 1, counts=counts
    ))

    # Step 6: Novelty
    novelty_content = gen.generate(_novelty_prompt(gen, gen.novelty, counts))

    # Step 7: Choose results structure based on whether benchmark exists
    benchmark_found = bool(re.search(r'(?:benchmark|base paper)', performance_evaluation, re.IGNORECASE))

    if benchmark_found:
        print("Benchmark section found — writing results with it.")
        result_sections = {
            "PERFORMANCE EVALUATION":      performance_evaluation,
            "WEB APP TESTING":             web_app_test,
            "SIGNIFICANCE OF KEY RESULTS": significance,
            "FAILED ATTEMPTS":             failed_attempts_content,
            "RESEARCH NOVELTY":            novelty_content,
        }
    else:
        print("No benchmark section — generating interpretation instead.")
        interp = gen.generate(_no_base_paper_prompt(gen, gen.code_summary, gen.result_summary, counts))
        result_sections = {
            "PERFORMANCE EVALUATION":      performance_evaluation,
            "WEB APP TESTING":             web_app_test,
            "SIGNIFICANCE OF KEY RESULTS": significance,
            "FAILED ATTEMPTS":             failed_attempts_content,
            "INTERPRETATION OF RESULTS":   interp,
            "RESEARCH NOVELTY":            novelty_content,
        }

    gen.save("OutputFiles/results.txt", result_sections, label="RESULTS")

    # Step 8: Conclusion
    conclusion = gen.generate(_conclusion_prompt(gen, gen.code_summary, gen.novelty, counts))

    # Step 9: Future Work
    future_work = gen.generate(_future_work_prompt(gen, gen.code_summary_val_specific, counts))

    gen.save(
        "OutputFiles/conclusion.txt",
        {"CONCLUSION": conclusion, "FUTURE WORK": future_work},
        label="CONCLUSION AND FUTURE WORK"
    )
