import sys
import os
import io
from pathlib import Path

# ── Ensure we can run from anywhere ──
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from doc_convertor.code import generate_docx

if __name__ == "__main__":
    print("🚀 Starting DOCX Generation Test...")
    
    # Define a exhaustive list of tokens to test all renderers
    tokens = [
        {"type": "doc_title", "text": "Test Dissertation Title"},
        {"type": "chapter", "num": 1, "text": "Introduction"},
        {"type": "subheading", "chapter_num": 1, "sub_num": 1, "text": "Background"},
        {"type": "body", "text": "This is a normal body paragraph with a citation (Smith, 2021).", "_warnings": ["[V2] Test warning"]},
        {"type": "bullet", "text": "Bullet point 1"},
        {"type": "bullet", "text": "Bullet point 2"},
        {"type": "h3", "text": "Specific Details"},
        {"type": "body", "text": "More text here."},
        {"type": "figure_ph", "ref": "1.1", "text": "Sample Figure Description"},
        {"type": "caption", "text": "Figure 1.1: A sample figure for testing."},
        {"type": "insight", "text": "This is an important insight extracted from the data."},
        {"type": "equation_ph", "text": "a^2 + b^2 = c^2"},
        {"type": "source", "text": "Source: Own elaboration."},
        {"type": "chapter", "num": None, "text": "REFERENCES"},
        {"type": "body", "text": "Smith, J. (2021). Testing dissertation generation. Journal of AI Workflows."}
    ]
    
    global_warnings = ["[V1] Duplicate citation test", "[V8] Missing reference test"]
    
    try:
        # Test all 4 formats
        for fmt in range(1, 5):
            output_file = f"OutputFiles/test_format_{fmt}.docx"
            os.makedirs("OutputFiles", exist_ok=True)
            print(f"  Generating format {fmt} -> {output_file}...")
            
            with open(output_file, "wb") as f:
                generate_docx(
                    tokens=tokens,
                    global_warnings=global_warnings,
                    output_path=f,
                    llm_analysis="Test AI analysis of issues.",
                    format=fmt
                )
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"  ✅ Format {fmt} generated successfully.")
            else:
                print(f"  ❌ Format {fmt} failed (file missing or empty).")
                
        print("\n🎉 All DOCX generation tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during DOCX generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
