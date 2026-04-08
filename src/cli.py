import argparse
from .models import AppConfig


def cli():
    """
    parser.parse_args()で
    args.functions_definition
    args.input,
    args.output,
    を作成
    """
    parser = argparse.ArgumentParser(description="Translate prompts "
                                     "into structured function calls.")

    parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json",
        help="Path to the function definitions JSON file."
    )
    parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json",
        help="Path to the input prompts JSON file.",
    )
    parser.add_argument(
        "--output",
        default="data/output/function_calling_results.json",
        help="Path to the output JSON file.",
    )
    args = parser.parse_args()
    return AppConfig(
        functions_definition=args.functions_definition,
        input=args.input,
        output=args.output
    )
