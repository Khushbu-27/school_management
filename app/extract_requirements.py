import os

def extract_requirements(root_dir, output_file):
    with open(output_file, "w") as f:
        f.write("# Project Requirements\n\n")
        
        for folder, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):  # Only process Python files
                    file_path = os.path.join(folder, file)
                    with open(file_path, "r") as code_file:
                        for line in code_file:
                            if "REQUIREMENT:" in line:  # Check for 'REQUIREMENT:' keyword
                                requirement = line.strip().replace("# REQUIREMENT:", "").strip()
                                f.write(f"- {requirement}\n")

root_dir = "C:\\Users\\DELL\\Desktop\\SMP(fastapi)\\project1\\app"

output_file = "REQUIREMENTS.md"
extract_requirements(root_dir, output_file)
print(f"Requirements extracted to {output_file}")
