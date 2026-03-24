"""
BaseGenerator — shared logic for all AutoThesis chapter generators.

Every chapter generator inherits this class and only needs to:
  1. Define `self.chapter_name` and `self.section_key` (matches config.yaml WORD_COUNTS key)
  2. Call `self.generate(prompt)` to get cleaned AI output
  3. Call `self.save(filepath, sections_dict)` to write output files safely
"""

from ai import generate_content
from utils import load_files, load_config, strip_markdown
from pathlib import Path
import os


class BaseGenerator:

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    def __init__(self, chapter_name: str, section_key: str):
        self.chapter_name = chapter_name
        self.section_key = section_key

        # Load config once
        self.config = load_config('config.yaml')
        self.format = int(self.config['FORMAT'])
        self.format_str = str(self.format)

        # Load all input files once
        (
            self.title,
            self.literature_review_summary,
            self.research_gaps,
            self.code_summary,
            self.web_app_summary,
            self.code_summary_val_specific,
            self.novelty,
            self.data_details,
            self.methodology,
            self.research_question_and_objectives,
            self.base_paper_summary,
            self.result_summary,
            self.failed_attempts,
            self.web_app_development,
            self.web_app_testing_results,
            self.prompt_parameters,
        ) = load_files()

    def get_counts(self) -> dict:
        """Return the word counts dict for this chapter and the active format."""
        return self.config['WORD_COUNTS'][self.format_str][self.section_key]

    def load_prompt(self, filename: str) -> str:
        """Load a prompt template from the prompts/ directory."""
        path = self.PROMPTS_DIR / filename
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate(self, prompt: str) -> str:
        """Call the AI, then strip any leaked Markdown from the output."""
        try:
            result = generate_content(prompt)
        except UnicodeEncodeError as e:
            print(f"Unicode error during generation: {e} — retrying with ASCII prompt.")
            result = generate_content(prompt.encode('ascii', 'ignore').decode('ascii'))
        return strip_markdown(result)

    def save(self, filepath: str, sections: dict, label: str = None) -> None:
        """Write sections to a file with UTF-8 → ASCII fallback."""
        label = label or self.chapter_name
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        def _write(encoding, errors):
            with open(filepath, "w", encoding=encoding, errors=errors) as f:
                f.write(f"{label}\n")
                f.write("------------------------\n")
                for i, (title, content) in enumerate(sections.items(), 1):
                    f.write(f"{i}. {title}\n")
                    f.write("-" * 40 + "\n")
                    safe = content if isinstance(content, str) else str(content)
                    f.write(safe + "\n\n")

        try:
            _write("utf-8", "replace")
            print(f"{label} written successfully → {filepath}")
        except Exception as e:
            print(f"UTF-8 failed ({e}), falling back to ASCII → {filepath}")
            _write("ascii", "replace")
