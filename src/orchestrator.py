import json

from .decoder import decode_json_object_for_prompt
from .errors import AppError
from .json_loader import load_function_definitions, load_prompt_items
from .llm_adapter import build_model
from .models import AppConfig, FunctionCallResult
from .writer import write_results


def run_pipeline(config: AppConfig) -> None:
    """
    仕事全体を進める人
    functionsを読み、promptを読み、decoderを呼び、結果をまとめる
    """
    functions = load_function_definitions(config.functions_definition)
    prompts = load_prompt_items(config.input)

    model = build_model()
    results: list[FunctionCallResult] = []

    for prompt in prompts:
        json_text = decode_json_object_for_prompt(
            model=model,
            prompt_text=prompt.prompt,
            functions=functions,
        )
        try:
            result_dict = json.loads(json_text)
        except json.JSONDecodeError as error:
            message = f"Failed to parse generated JSON: {json_text}"
            raise AppError(message) from error
        print(result_dict)
        results.append(FunctionCallResult(**result_dict))
    write_results(config.output, results)
