# 道具箱
try:
    from llm_sdk import Small_LLM_Model
except ImportError:  # Fallback for the local source tree layout.
    from llm_sdk.llm_sdk import Small_LLM_Model


def build_model(model_name: str = "Qwen/Qwen3-0.6B") -> Small_LLM_Model:
    return Small_LLM_Model(model_name=model_name)


def encode_text(model: Small_LLM_Model, text: str) -> list[int]:
    token_tensor = model.encode(text)
    return token_tensor[0].tolist()


def decode_tokens(model: Small_LLM_Model, ids: list[int]) -> str:
    return model.decode(ids)


def get_next_token_logits(
    model: Small_LLM_Model,
    input_ids: list[int],
) -> list[float]:
    return model.get_logits_from_input_ids(input_ids)


def build_token_texts(
        model: Small_LLM_Model,
        logits: list[float]
        ) -> dict[int, str]:
    token_texts = {}

    for token_id, _ in enumerate(logits):
        token_texts[token_id] = decode_tokens(model, [token_id])

    return token_texts


def generate_traditional_response(
        model: Small_LLM_Model,
        input_ids: list[int],
) -> str:
    max_new_tokens = 40
    generated_ids: list[int] = []
    for _ in range(max_new_tokens):
        logits = get_next_token_logits(model, input_ids)
        token_id = max(range(len(logits)), key=lambda i: logits[i])
        generated_ids.append(token_id)
        input_ids.append(token_id)

    return decode_tokens(model, generated_ids)
