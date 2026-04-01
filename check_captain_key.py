import json
import glob
from pathlib import Path

files = glob.glob(r'c:\Users\Sai Krishna\OneDrive\Desktop\IPL\ipl_json\*.json')
found = False
for f in files[:100]: # Check first 100
    with open(f, 'r') as jf:
        data = json.load(jf)
        info = data.get('info', {})
        if 'captains' in info or 'captain' in info:
            print(f"Found in {f}: {info.get('captains') or info.get('captain')}")
            found = True
            break
if not found:
    print("No captain/captains key found in first 100 JSON files.")
