import sys
import os
from pathlib import Path

# ── Ensure we can run from anywhere ──
# Set CWD to project root and add to sys.path
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from generators.result_gen import generate_result_conclusion

if __name__ == "__main__":
    print("🚀 Starting Results & Conclusion Generation Test...")
    try:
        generate_result_conclusion()
        print("\n✅ Success! Results saved to OutputFiles/results.txt and Conclusion to OutputFiles/conclusion.txt")
    except Exception as e:
        print(f"\n❌ Error during Results generation: {e}")
