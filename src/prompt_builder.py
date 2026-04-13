from .models import FunctionDefinition


def build_number_parameter_prompt(user_prompt: str, target: str) -> str:
    lines = [
        "Extract the value for one parameter.",
        "Function: fn_add_numbers",
        f"Target parameter: {target}",
        "Parameter type: number",
        "Return only the number.",
        f"User request: {user_prompt}",
        "Value:",
    ]
    lines.append(user_prompt)
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
