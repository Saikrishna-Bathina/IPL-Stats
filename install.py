import sys
import subprocess
import os

print(f"Using Python executable: {sys.executable}")
print(f"Current Path: {os.environ.get('PATH')}")

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Successfully installed requirements.")
except Exception as e:
    print(f"Failed to install requirements via subrocess pip: {e}")
