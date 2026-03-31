import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.implementation_gen import generate_implementation_toc, generate_implementation_content

if __name__ == "__main__":
    print("🚀 Starting Implementation Generation Test...")
    try:
        toc_text = generate_implementation_toc()
        generate_implementation_content(toc_text)
        print("\n✅ Success! Implementation generated and saved to OutputFiles/implementation.txt")
    except Exception as e:
        print(f"\n❌ Error during Implementation generation: {e}")
