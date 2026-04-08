from .json_loader import load_function_definitions, load_prompt_items
from .models import AppConfig


def run_pipeline(config: AppConfig) -> None:
    """
    パスを
    """
    functions = load_function_definitions(config.functions_definition)
    prompts = load_prompt_items(config.input)

    print(f"Loaded {len(functions)} functions.")
    print(f"Loaded {len(prompts)} prompts.")
