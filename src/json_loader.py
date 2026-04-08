from .models import FunctionDefinition, PromptItem
import json
from .errors import InputFileError


def read_json_file(file_path: str) -> list[dict]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as error:
        raise InputFileError(f"Input file not found: {file_path}") from error
    except json.JSONDecodeError as error:
        raise InputFileError(f"Invalid JSON in file: {file_path}") from error

    if not isinstance(data, list):
        raise InputFileError(f"Expected a JSON array in file: {file_path}")

    return data


def load_function_definitions(file_path: str) -> list[FunctionDefinition]:
    """
    make function's instances
    """
    data = read_json_file(file_path)
    functions = []

    for item in data:
        # name=item["name"],
        # description=item["description"],
        # parameters=item["parameters"],
        # returns=item["returns"],
        # ** -> dictionary unpacking
        functions.append(FunctionDefinition(**item))
    return functions


def load_prompt_items(file_path: str) -> list[PromptItem]:
    """
    make prompt's instances
    """
    data = read_json_file(file_path)
    result = []
    for item in data:
        # prompt=item["prompt"]
        result.append(PromptItem(**item))
    return result
