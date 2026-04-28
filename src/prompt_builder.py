from .models import FunctionDefinition


def build_json_generation_context(
    functions: list[FunctionDefinition],
    user_prompt: str,
) -> str:
    """Build the prompt used for full JSON generation."""
    function_lines = []

    for function in functions:
        parameter_lines = []
        for parameter_name, parameter_definition in (
            function.parameters.items()
        ):
            parameter_lines.append(
                f"{parameter_name}: {parameter_definition.type}"
            )

        function_lines.append(
            (
                f"- name: {function.name}\n"
                f"  description: {function.description}\n"
                f"  parameters: {', '.join(parameter_lines)}"
            )
        )

    return "\n".join(
        [
            "You are generating one JSON object for function calling.",
            "The JSON object must contain exactly these keys:",
            '1. "prompt"',
            '2. "name"',
            '3. "parameters"',
            "Choose the best function for the user request.",
            "Do not answer the request.",
            "Do not compute the function result.",
            "Generate only argument values needed to call the function.",
            "For string arguments, copy literal text from the user request",
            "when the argument asks for existing text.",
            "For replacement strings, output only the replacement text",
            "itself.",
            "For regex strings, output the smallest pattern that matches one",
            "target occurrence. Do not include surrounding text and do not",
            "add .* just because the target appears multiple times.",
            "For common regex requests, use normal regex notation: digits or",
            "numbers use [0-9]+, vowels use [aeiouAEIOU], whitespace uses",
            "\\s+.",
            "Never output a plain character list as regex. For vowels, output",
            "[aeiouAEIOU], not aeiouAEIOU.",
            "For numbers, output [0-9]+, not ([0-9]+)|([0-9]+).",
            "Examples for regex replacement arguments:",
            "Replace all numbers in \"a 12 b\" with X -> regex [0-9]+,",
            "replacement X.",
            "Replace vowels in \"hello\" with asterisks -> regex",
            "[aeiouAEIOU], replacement *.",
            "Substitute the word 'cat' with 'dog' -> regex cat,",
            "replacement dog.",
            "Available functions:",
            *function_lines,
            f"User request: {user_prompt}",
            "JSON object:",
        ]
    )
