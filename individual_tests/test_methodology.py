import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.methodology_gen import generate_methodology_toc, generate_methodology_content

if __name__ == "__main__":
    print("🚀 Starting Methodology Generation Test...")
    try:
        # print("📝 Generating Methodology TOC...")
        # toc = generate_methodology_toc()

        print("📝 Reading Saved Methodology TOC...")
        with open("InputFiles/methodology_toc_content.txt", "r", encoding="utf-8") as f:
            toc = f.read()
        print("\nSaved TOC:")
        print(toc)
        
        print("\n🚧 Generating Methodology Content...")
        generate_methodology_content(toc)
        
        print("\n✅ Success! Methodology generated and saved to OutputFiles/methodology.txt")
    except Exception as e:
        print(f"\n❌ Error during Methodology generation: {e}")
