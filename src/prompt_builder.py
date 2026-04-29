import json

from .models import FunctionDefinition


def build_json_generation_context(
    functions: list[FunctionDefinition],
    user_prompt: str,
) -> str:
    """Build the prompt used for full JSON generation."""
    function_payload = [
        function.model_dump()
        for function in functions
    ]

    return "\n".join(
        [
            "You are a strict AI assistant for function calling.",
            "Analyze the user request and prepare a function call.",
            "Do not answer the request.",
            "Do not compute the function result.",
            "",
            "[Available Functions]",
            json.dumps(function_payload, ensure_ascii=False, indent=2),
            "",
            "[Rules]",
            "1. Choose exactly one function from Available Functions.",
            "2. Extract only the required parameters for that function.",
            "3. Match each parameter type exactly.",
            "4. For string parameters that refer to existing text, copy the",
            "   literal text from the user request.",
            "5. For replacement parameters, output the literal replacement",
            "   value. If it is described as a symbol, output one symbol",
            "   character, not the English name or a repeated sequence.",
            "6. For regex parameters, output the smallest useful regex.",
            "   Do not add anchors, capture groups, or extra repetitions",
            "   unless explicitly requested.",
            "7. For repeated categories, use one repeated regex pattern, not",
            "   alternatives.",
            "",
            "[User Prompt]",
            user_prompt,
            "",
            "JSON object:",
        ]
    )
