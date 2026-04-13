from .decoder import decode_function_name, decode_string_parameter, decode_number_parameter
from .json_loader import load_function_definitions, load_prompt_items
from .llm_adapter import build_model, encode_text
from .models import AppConfig, FunctionDefinition
from .prompt_builder import build_function_name_prompt, build_number_parameter_prompt, build_string_parameter_prompt
from .errors import AppError


try:
    from llm_sdk import Small_LLM_Model
except ImportError:  # Fallback for the local source tree layout.
    from llm_sdk.llm_sdk import Small_LLM_Model


def find_function_by_name(
        functions: list[FunctionDefinition],
        name: str
        ) -> FunctionDefinition:
    for function in functions:
        if function.name == name:
            return function
    raise AppError("Function not found")


def decode_parameters_for_function(
        model: Small_LLM_Model,
        user_prompt: str,
        function_def: FunctionDefinition
        ) -> dict[str, object]:
    parameters = {}
    for param_name, param_def in function_def.parameters.items():
        if param_def.type == "number":
            prompt_text = build_number_parameter_prompt(user_prompt,
                                                        param_name)
            input_ids = encode_text(model, prompt_text)
            value = decode_number_parameter(model, input_ids)
        elif param_def.type == "string":
            prompt_text = build_string_parameter_prompt(user_prompt,
                                                        param_name)
            input_ids = encode_text(model, prompt_text)
            value = decode_string_parameter(model, input_ids)
        else:
            raise AppError(f"Unsupported parameter type: {param_def.type}")

        parameters[param_name] = value

    return parameters


def run_pipeline(config: AppConfig) -> None:
    """
    仕事全体を進める人
    functionsを読み、promptを読み、decoderを呼び、結果をまとめる
    """
    functions = load_function_definitions(config.functions_definition)
    prompts = load_prompt_items(config.input)

    model = build_model()
    candidates = [function.name for function in functions]

    print()

    print("=== Testing LLM with function calling ===")
    for prompt in prompts:
        prompt_text = build_function_name_prompt(functions, prompt.prompt)
        input_ids = encode_text(model, prompt_text)
        name = decode_function_name(model, input_ids, candidates)

        selected_function = find_function_by_name(functions, name)

        parameters = decode_parameters_for_function(
            model=model,
            user_prompt=prompt.prompt,
            function_def=selected_function
        )

        result = {
            "prompt": prompt.prompt,
            "name": name,
            "parameters": parameters
        }

        print(result)
    # print("=== Testing tradtional function of LLM ===")
    # for prompt in prompts:
    #     prompt_text = f"{prompt.prompt}, respond simple like"
    #     " 'The sum of 40 and 2 is 42.'"
    #     input_ids = encode_text(model, prompt_text)
    #     result = generate_traditional_response(model, input_ids)
    #     print(prompt.prompt, result)
