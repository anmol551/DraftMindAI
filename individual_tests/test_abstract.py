import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.abstract_gen import generate_abstract

if __name__ == "__main__":
    print("🚀 Starting Abstract Generation Test...")
    try:
        content = generate_abstract()
        print("\n✅ Success! Abstract generated and saved to OutputFiles/abstract.txt")
        print("-" * 50)
        print(content[:200] + "...")
        print("-" * 50)
    except Exception as e:
        print(f"\n❌ Error during Abstract generation: {e}")
