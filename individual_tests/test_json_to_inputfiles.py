import os
import json
import sys

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_text_file

def _list_to_str(val):
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    if isinstance(val, dict):
        return json.dumps(val, indent=2)
    return str(val) if val is not None else ""

def _extract_result_plot_summary(val):
    if isinstance(val, dict) and "table" in val:
        rows = []
        for row in val["table"]:
            rows.append(
                f"Plot {row.get('Plot_Number','')}: {row.get('Title','')} | "
                f"Type: {row.get('Type','')} | Insights: {row.get('Insights','')}"
            )
        return "\n\n".join(rows)
    return _list_to_str(val)

def _extract_result_table(val):
    if not isinstance(val, dict):
        return _list_to_str(val)
    lines = []
    for table_key, table_data in val.items():
        if isinstance(table_data, dict):
            lines.append(f"\n### {table_key.replace('_', ' ').title()}")
            note = table_data.get("note", "")
            if note:
                lines.append(f"Note: {note}")
            cols = table_data.get("columns", [])
            rows = table_data.get("rows", [])
            if cols:
                lines.append(" | ".join(cols))
                lines.append(" | ".join(["---"] * len(cols)))
            for row in rows:
                lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)

def _extract_code_summary_with_values(val):
    if isinstance(val, dict):
        return json.dumps(val, indent=2)
    return _list_to_str(val)

def main():
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Temp", "output.json")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        print(f"Successfully loaded {json_path}")
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return

    def default(key, fallback="", transform=None):
        if key in json_data:
            val = json_data[key]
            if transform:
                return transform(val)
            return _list_to_str(val)
        return fallback

    title          = default("title")
    question       = default("research_question")
    objective      = default("research_objectives", transform=lambda v: "\n".join(v) if isinstance(v, list) else _list_to_str(v))
    data_details   = default("data_details")
    pipeline_val   = default("code_pipeline")

    literature_review_summary = default("literature_review_summary")
    research_gaps             = default("research_gap")
    base_paper_summary        = default("base_paper_summary")
    base_paper_citation       = default("base_paper_reference")
    code_summary              = default("code_summary")
    code_summary_with_values  = default("code_summary_with_values", transform=_extract_code_summary_with_values)
    webapp_summary            = default("web_app_summary")
    webapp_test               = default("web_app_test_cases")
    novelty                   = default("novelty")
    result_plot_summary       = default("result_plot_summary", transform=_extract_result_plot_summary)
    result_table_summary      = default("result_table", transform=_extract_result_table)
    failed_attempt_summary    = default("failed_attempts")

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "InputFiles")
    os.makedirs(output_dir, exist_ok=True)
    
    save_text_file(data_details,      os.path.join(output_dir, "dd.txt"))
    save_text_file(pipeline_val,      os.path.join(output_dir, "pipeline.txt"))
    save_text_file(literature_review_summary, os.path.join(output_dir, "lrs.txt"))
    save_text_file(research_gaps,     os.path.join(output_dir, "rg.txt"))
    save_text_file(base_paper_summary,os.path.join(output_dir, "bps.txt"))
    save_text_file(code_summary,      os.path.join(output_dir, "cs.txt"))
    save_text_file(code_summary_with_values, os.path.join(output_dir, "csvs.txt"))
    save_text_file(webapp_summary,    os.path.join(output_dir, "ws.txt"))
    save_text_file(webapp_test,       os.path.join(output_dir, "wat.txt"))
    save_text_file(novelty,           os.path.join(output_dir, "novelty.txt"))
    save_text_file(result_plot_summary + "\n\n" + result_table_summary, os.path.join(output_dir, "rs.txt"))
    save_text_file(result_plot_summary + "\n\n" + failed_attempt_summary, os.path.join(output_dir, "fa.txt"))

    print(f"Successfully extracted data from JSON and saved to {output_dir}")

if __name__ == "__main__":
    main()
