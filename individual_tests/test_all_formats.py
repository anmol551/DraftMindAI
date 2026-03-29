import subprocess
import os

def test_all_formats():
    input_file = "/home/miko/Documents/GitHub/AutoThesis/Temp/temp.txt"
    output_dir = "/home/miko/Documents/GitHub/AutoThesis/OutputFiles"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for fmt in range(1, 5):
        output_file = os.path.join(output_dir, f"test_format_{fmt}.docx")
        print(f"\n--- Generating Format {fmt} ---")
        
        # Run code.py with --no-llm to speed up the test and avoid API costs/errors
        cmd = [
            "python3", 
            "/home/miko/Documents/GitHub/AutoThesis/doc_convertor/code.py", 
            input_file, 
            output_file, 
            "--format", str(fmt),
            "--no-llm"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout)
            print(f"Successfully generated: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating format {fmt}:")
            print(e.stderr)

if __name__ == "__main__":
    test_all_formats()
