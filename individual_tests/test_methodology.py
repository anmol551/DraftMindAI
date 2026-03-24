import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.methodology_gen import generate_methodology

if __name__ == "__main__":
    print("🚀 Starting Methodology Generation Test...")
    try:
        generate_methodology()
        print("\n✅ Success! Methodology generated and saved to OutputFiles/methodology.txt")
    except Exception as e:
        print(f"\n❌ Error during Methodology generation: {e}")
