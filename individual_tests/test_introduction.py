import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.introduction_gen import generate_introduction

if __name__ == "__main__":
    print("🚀 Starting Introduction Generation Test...")
    try:
        generate_introduction()
        print("\n✅ Success! Introduction generated and saved to OutputFiles/introduction.txt")
    except Exception as e:
        print(f"\n❌ Error during Introduction generation: {e}")
