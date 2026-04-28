import json

from .errors import DecodeError
from .llm_adapter import decode_tokens, encode_text, get_next_token_logits
from .models import FunctionDefinition
from .prompt_builder import build_json_generation_context

try:
    from llm_sdk import Small_LLM_Model
except ImportError:  # Fallback for the local source tree layout.
    from llm_sdk.llm_sdk import Small_LLM_Model


MAX_REGEX_STRING_TOKENS = 32
MAX_REPLACEMENT_STRING_TOKENS = 16
MAX_GENERAL_STRING_TOKENS = 120
MAX_NUMBER_TOKENS = 12


def _best_token(logits: list[float], allowed: set[int]) -> int:
    """Return the highest-scoring token among allowed token ids."""
    if not allowed:
        raise DecodeError("No valid token found during decoding.")
    return max(allowed, key=lambda token_id: logits[token_id])


def _token_texts(
    model: Small_LLM_Model,
    vocab_size: int,
    cache: dict[int, str],
) -> dict[int, str]:
    """Cache token-id to text mapping for one decoding run."""
    if not cache:
        cache.update(
            {
                token_id: decode_tokens(model, [token_id])
                for token_id in range(vocab_size)
            }
        )
    return cache


def _emit(
    model: Small_LLM_Model,
    input_ids: list[int],
    text: str,
) -> str:
    """Append known JSON text to the decoding context."""
    input_ids.extend(encode_text(model, text))
    return text


def _decode_choice(
    model: Small_LLM_Model,
    input_ids: list[int],
    candidates: list[str],
) -> str:
    """Decode one value from a fixed list of candidate strings."""
    sequences = [
        (candidate, encode_text(model, candidate))
        for candidate in candidates
    ]
    generated: list[int] = []

    while True:
        for candidate, token_ids in sequences:
            if generated == token_ids:
                input_ids.extend(generated)
                return candidate

        allowed: set[int] = set()
        for _, token_ids in sequences:
            if token_ids[:len(generated)] == generated:
                if len(token_ids) > len(generated):
                    allowed.add(token_ids[len(generated)])

        logits = get_next_token_logits(model, input_ids + generated)
        generated.append(_best_token(logits, allowed))


def _safe_string_token(text: str) -> bool:
    """Return whether a token can be placed inside a simple JSON string."""
    if not text:
        return False
    if '"' in text or "\\" in text:
        return False
    return all(character >= " " for character in text)


def _balanced_regex(text: str) -> bool:
    """Return whether brackets and parentheses are balanced enough to stop."""
    square_depth = 0
    round_depth = 0

    for character in text:
        if character == "[":
            square_depth += 1
        elif character == "]":
            square_depth -= 1
        elif character == "(":
            round_depth += 1
        elif character == ")":
            round_depth -= 1
        if square_depth < 0 or round_depth < 0:
            return False

    if square_depth != 0 or round_depth != 0:
        return False
    return text[-1] not in {"|", "(", "[", "."}


def _plain_literal(text: str) -> bool:
    """Return whether the regex generated so far is just literal text."""
    return text.isalnum() or (
        "_" in text and text.replace("_", "").isalnum()
    )


def _should_close_string(
    value: str,
    next_text: str,
    parameter_name: str,
) -> bool:
    """Close short generated values before the model starts rambling."""
    if not value:
        return False

    stripped = value.strip()
    next_stripped = next_text.strip()

    if parameter_name == "regex":
        if not _balanced_regex(stripped):
            return False
        if next_text[:1].isspace():
            return True
        if next_stripped[:1] in {"|", ",", "["}:
            return True
        if next_stripped[:1] == "." and _plain_literal(stripped):
            return True
        if next_stripped in {"or", "and", "with", "in"}:
            return True

    if parameter_name == "replacement":
        if next_text[:1].isspace():
            return True
        if next_stripped[:1] in {"?", ".", ",", ";", ":", "!"}:
            return True
        if stripped in {"*", "_", "-", "+"}:
            return next_stripped[:1] in {"*", "_", "-", "+", "?"}

    return False


def _string_token_limit(parameter_name: str) -> int:
    """Keep short parameter values from running until the global limit."""
    if parameter_name == "regex":
        return MAX_REGEX_STRING_TOKENS
    if parameter_name == "replacement":
        return MAX_REPLACEMENT_STRING_TOKENS
    return MAX_GENERAL_STRING_TOKENS


def _decode_string(
    model: Small_LLM_Model,
    input_ids: list[int],
    parameter_name: str,
    token_text_cache: dict[int, str],
) -> str:
    """Decode a JSON string value while keeping the JSON syntax valid."""
    quote_ids = encode_text(model, '"')
    if len(quote_ids) != 1:
        raise DecodeError("Quote token must be represented by one token.")

    quote_id = quote_ids[0]
    generated: list[int] = []
    parts = [_emit(model, input_ids, '"')]

    for _ in range(_string_token_limit(parameter_name)):
        logits = get_next_token_logits(model, input_ids + generated)
        # ==== logitsの中身を全部decodeしてtoken_idと実際の文字列のセットを作る ====
        token_texts = _token_texts(model, len(logits), token_text_cache)
        value = decode_tokens(model, generated)
        allowed: set[int] = set()

        # ==== logitsの中から選択可能な次の選択肢を絞る ====
        for token_id, token_text in token_texts.items():
            if token_id == quote_id:
                if value:
                    allowed.add(token_id)
                continue
            if not _safe_string_token(token_text):
                continue
            if not value and token_text[0].isspace():
                continue
            allowed.add(token_id)

        token_id = _best_token(logits, allowed)
        token_text = token_texts[token_id]

        if token_id == quote_id or _should_close_string(
            value,
            token_text,
            parameter_name,
        ):
            input_ids.extend(generated)
            parts.append(value)
            parts.append(_emit(model, input_ids, '"'))
            return "".join(parts)

        generated.append(token_id)

    value = decode_tokens(model, generated)
    # ==== 中身があるなら無理やり " で閉じて返す ====
    if value:
        input_ids.extend(generated)
        parts.append(value)
        parts.append(_emit(model, input_ids, '"'))
        return "".join(parts)
    raise DecodeError("Failed to finish JSON string value.")


def _valid_number_prefix(text: str) -> bool:
    """Return whether text can still become a JSON number."""
    if not text:
        return False
    if any(character not in "-.0123456789" for character in text):
        return False
    if text.count("-") > 1 or ("-" in text and not text.startswith("-")):
        return False
    if text.count(".") > 1:
        return False

    body = text[1:] if text.startswith("-") else text
    if body in {"", "."}:
        return body == ""
    if len(body) > 1 and body[0] == "0" and body[1] != ".":
        return False
    return any(character.isdigit() for character in body)


def _complete_number(text: str) -> bool:
    """Return whether text is a complete JSON number."""
    return (
        _valid_number_prefix(text)
        and text not in {"-", ".", "-."}
        and not text.endswith(".")
        and any(character.isdigit() for character in text)
    )


def _decode_number(
    model: Small_LLM_Model,
    input_ids: list[int],
    terminators: list[str],
    token_text_cache: dict[int, str],
) -> str:
    """Decode a JSON number value."""
    generated: list[int] = []
    terminator_ids = {
        ids[0]
        for terminator in terminators
        if len(ids := encode_text(model, terminator)) == 1
    }

    for _ in range(MAX_NUMBER_TOKENS):
        logits = get_next_token_logits(model, input_ids + generated)
        token_texts = _token_texts(model, len(logits), token_text_cache)
        value = decode_tokens(model, generated)
        allowed: set[int] = set()

        if _complete_number(value):
            allowed.update(terminator_ids)

        for token_id, token_text in token_texts.items():
            if _valid_number_prefix(value + token_text):
                allowed.add(token_id)

        token_id = _best_token(logits, allowed)
        if token_id in terminator_ids:
            input_ids.extend(generated)
            return value
        generated.append(token_id)

    value = decode_tokens(model, generated)
    if _complete_number(value):
        input_ids.extend(generated)
        return value
    raise DecodeError("Failed to finish JSON number value.")


def _decode_value(
    model: Small_LLM_Model,
    input_ids: list[int],
    value_type: str,
    parameter_name: str,
    terminators: list[str],
    token_text_cache: dict[int, str],
) -> str:
    """Decode one value according to the parameter type."""
    if value_type == "string":
        return _decode_string(
            model,
            input_ids,
            parameter_name,
            token_text_cache,
        )
    if value_type == "number":
        return _decode_number(
            model,
            input_ids,
            terminators,
            token_text_cache,
        )
    if value_type == "boolean":
        return _decode_choice(model, input_ids, ["true", "false"])
    raise DecodeError(f"Unsupported parameter type: {value_type}")


def _decode_parameters(
    model: Small_LLM_Model,
    input_ids: list[int],
    function_def: FunctionDefinition,
    token_text_cache: dict[int, str],
) -> str:
    """Decode the parameters object for the selected function."""
    parts = [_emit(model, input_ids, "{")]
    items = list(function_def.parameters.items())

    # ==== 選ばれた関数が持つ全てのパラメータに対して処理を行う ====
    for index, (name, definition) in enumerate(items):
        if index > 0:
            parts.append(_emit(model, input_ids, ","))
        parts.append(_emit(model, input_ids, json.dumps(name)))
        parts.append(_emit(model, input_ids, ":"))
        terminator = "," if index < len(items) - 1 else "}"
        parts.append(
            _decode_value(
                model,
                input_ids,
                definition.type,
                name,
                [terminator],
                token_text_cache,
            )
        )

    parts.append(_emit(model, input_ids, "}"))
    return "".join(parts)


def decode_json_object_for_prompt(
    model: Small_LLM_Model,
    prompt_text: str,
    functions: list[FunctionDefinition],
) -> str:
    """
    Decode one schema-valid function-call JSON object.
    関数を選択するための関数
    """
    input_ids = encode_text(
        model,
        build_json_generation_context(functions, prompt_text),
    )
    token_text_cache: dict[int, str] = {}
    parts: list[str] = []

# ==== JSON確定部分の組み立て ====

    parts.append(_emit(model, input_ids, "{"))
    parts.append(_emit(model, input_ids, '"prompt"'))
    parts.append(_emit(model, input_ids, ":"))
    parts.append(_emit(model, input_ids, json.dumps(prompt_text)))
    parts.append(_emit(model, input_ids, ","))
    parts.append(_emit(model, input_ids, '"name"'))
    parts.append(_emit(model, input_ids, ":"))

# ==== 関数一覧をJSON文字列（'"fn_greet"'）として作成 ====
    function_names = [json.dumps(function.name) for function in functions]
# ==== LLMを呼び出して適切な関数を選択 ====
    selected_name_json = _decode_choice(model, input_ids, function_names)
# ==== JSON文字列をPythonの文字列に戻す ====
    selected_name = json.loads(selected_name_json)
    parts.append(selected_name_json)

# ==== 選ばれた関数名に対応するインスタンスを探す ====
    selected_function = next(
        function for function in functions if function.name == selected_name
    )

    parts.append(_emit(model, input_ids, ","))
    parts.append(_emit(model, input_ids, '"parameters"'))
    parts.append(_emit(model, input_ids, ":"))
    parts.append(
        # ==== パラメータの抽出 ====
        _decode_parameters(
            model,
            input_ids,
            selected_function,
            token_text_cache,
        )
    )
    parts.append(_emit(model, input_ids, "}"))

    return "".join(parts)
