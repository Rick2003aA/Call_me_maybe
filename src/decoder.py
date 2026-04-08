from .llm_adapter import get_next_token_logits
from .errors import DecodeError


def is_valid_prefix(generated: str, candidates: list[str]) -> bool:
    for candidate in candidates:
        if candidate.startswith(generated):
            return True
    return False


def choose_token(
        generated: str,
        candidates: list[str],
        logits: list[float],
        token_texts: dict[int, str]
         ) -> int:
    best_token_id = -1
    best_score = float("-inf")
    for token_id, score in enumerate(logits):
        next_text = generated + token_texts[token_id]

        if is_valid_prefix(next_text, candidates):
            if score > best_score:
                best_score = score
                best_token_id = token_id

    return best_token_id
