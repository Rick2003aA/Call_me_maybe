from .models import FunctionDefinition


def build_string_parameter_prompt(
        user_prompt: str,
        function_name: str,
        target: str
        ) -> str:
    lines = [
        f"Request: {user_prompt}",
        f"Function: {function_name}",
        f"Return only the value of parameter {target}.",
        "Value:",
    ]
    return "\n".join(lines)


def build_number_parameter_prompt(
    user_prompt: str,
    function_name: str,
    target: str
) -> str:
    if target == "a":
        instruction = "Extract the first number."
    elif target == "b":
        instruction = "Extract the second number."
    else:
        instruction = f"Return parameter {target}."

    lines = [
        f"Request: {user_prompt}",
        f"Function: {function_name}",
        instruction,
        "Return only the number.",
        "Value:",
    ]
    return "\n".join(lines)


def build_function_name_prompt(
    functions: list[FunctionDefinition],
    user_prompt: str,
) -> str:
    lines = [
        "Choose the best function name for the user request.",
        "Return only the function name.",
        "Available functions:",
    ]

    for function in functions:
        lines.append(f"- {function.name}: {function.description}")

    lines.append(f"User request: {user_prompt}")
    lines.append("Function name:")

    return "\n".join(lines)
