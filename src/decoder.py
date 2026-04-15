import re

try:
    from llm_sdk import Small_LLM_Model
except ImportError:  # Fallback for the local source tree layout.
    from llm_sdk.llm_sdk import Small_LLM_Model

from .errors import DecodeError
from .llm_adapter import decode_tokens, encode_text, get_next_token_logits

# LLM に「次どうしたい？」と聞く
# LLM が返した候補表を見る
# でもルールに合う token だけ残す
# その中で一番良い token を選ぶ
# 1個進める
# 関数名が完成するまで繰り返す


def build_candidate_sequences(
    model: Small_LLM_Model,
    candidates: list[str],
) -> list[tuple[str, list[int]]]:
    sequences = []

    # Try a few common output prefixes so decoding can start after
    # a prompt-ending space, colon, or newline.
    for candidate in candidates:
        for prefix in ("", " ", "\n"):
            sequences.append((candidate,
                              encode_text(model, prefix + candidate)))

    return sequences


def choose_token(
    generated_ids: list[int],
    candidate_sequences: list[tuple[str, list[int]]],
    logits: list[float],
) -> int:
    """
    候補:

    [
        ("fn_add_numbers", [11, 22, 33]),
        ("fn_greet", [11, 44]),
    ]

    今:
    generated_ids = [11]
    logits の一部がこうだとします。

    logits[22] = 8.0
    logits[44] = 6.0
    logits[99] = 100.0

    このとき 99 は score がめちゃくちゃ高くてもダメです。
    なぜなら 99 はどの候補の次にも必要ないからです。

    受け入れられるのは 22 と 44 だけです。

    だから最終的に選ばれるのは 22 です。
    """
    allowed_token_ids: set[int] = set()

    for _, token_ids in candidate_sequences:
        prefix_length = len(generated_ids)

        if token_ids[:prefix_length] != generated_ids:
            continue

        if len(token_ids) > prefix_length:
            allowed_token_ids.add(token_ids[prefix_length])

    if not allowed_token_ids:
        raise DecodeError("No valid token found for function name decoding.")

    return max(allowed_token_ids, key=lambda token_id: logits[token_id])


def decode_function_name(
    model: Small_LLM_Model,
    input_ids: list[int],
    candidates: list[str],
) -> str:
    """
    input_ids: LLMに見せる全文
    generated_ids: 生成された関数名
    """
    candidate_sequences = build_candidate_sequences(model, candidates)
    generated_ids: list[int] = []

    while True:
        """
        生成したものが関数名と一致する or 見つからない場合に止まる
        """
        for candidate, token_ids in candidate_sequences:
            if token_ids == generated_ids:
                return candidate

        logits = get_next_token_logits(model, input_ids)
        token_id = choose_token(generated_ids, candidate_sequences, logits)
        generated_ids.append(token_id)
        input_ids.append(token_id)


# ==== パラメーター抽出のための機能 ====


def generate_greedy_text(
    model: Small_LLM_Model,
    input_ids: list[int],
    max_new_tokens: int = 8,
) -> str:
    # パラメーター抽出では、まず短く自由生成してから Python 側で値を読む。
    generated_ids: list[int] = []
    working_input_ids = input_ids.copy()

    for _ in range(max_new_tokens):
        logits = get_next_token_logits(model, working_input_ids)
        token_id = max(range(len(logits)), key=lambda i: logits[i])
        generated_ids.append(token_id)
        working_input_ids.append(token_id)

        text = decode_tokens(model, generated_ids)
        if "\n" in text:
            break

    return decode_tokens(model, generated_ids)


def decode_number_parameter(
    model: Small_LLM_Model,
    input_ids: list[int]
) -> int:
    text = generate_greedy_text(model, input_ids)
    match = re.search(r"-?\d+", text)

    if match is None:
        raise DecodeError(f"Failed to decode number parameter: {text}")

    return int(match.group())


def decode_string_parameter(
        model: Small_LLM_Model,
        input_ids: list[int]
        ) -> str:
    text = generate_greedy_text(model, input_ids, max_new_tokens=16).strip()

    if not text:
        raise DecodeError("Failed to decode string parameter.")

    # 文字列の前後に quote があれば落として扱いやすくする。
    return text.strip("\"'")
