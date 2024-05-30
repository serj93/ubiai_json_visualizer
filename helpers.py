import json
import glob

from typing import List, Dict, Optional


def read_file(filename: str) -> Optional[str]:
    try:
        with open(file=filename) as file:
            result = file.read().rstrip()
    except Exception as e:
        print(e)
        result = None
    return result


def loads_json(data: str) -> List[Dict]:
    try:
        result = json.loads(data)
    except Exception as e:
        result = []
        print(e)
    return result


def find_files(path_pattern: str) -> List[str]:
    return glob.glob(path_pattern)
