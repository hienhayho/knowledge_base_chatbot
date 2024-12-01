import subprocess

# Define the input requirements file and output file
input_file = "requirements.txt"
output_file = "actual_requirements.txt"

# Read the packages from the requirements file
with open(input_file, "r") as file:
    required_packages = [
        line.strip().split("==")[0]
        for line in file
        if line.strip() and not line.startswith("#")
    ]

# Get the list of installed packages and their versions
installed_packages = subprocess.run(
    ["pip", "list", "--format=freeze"], capture_output=True, text=True
).stdout.splitlines()

# Filter the installed packages to match the required ones
filtered_packages = [
    pkg for pkg in installed_packages if pkg.split("==")[0] in required_packages
]

# Write the filtered packages to the output file
with open(output_file, "w") as file:
    file.write("\n".join(filtered_packages))

print(f"Filtered package list saved to {output_file}")
