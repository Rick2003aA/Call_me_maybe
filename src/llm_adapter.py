from llm_sdk import Small_LLM_Model


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


if __name__ == "__main__":
    sample_text = "What is the sum of 2 and 3?"

    try:
        model = build_model()
        input_ids = encode_text(model, sample_text)
        decoded_text = decode_tokens(model, input_ids)
        logits = get_next_token_logits(model, input_ids)
    except Exception as error:
        print(f"Experiment failed: {error}")
    else:
        print("sample_text:", sample_text)
        print("input_ids:", input_ids)
        print("input_ids type:", type(input_ids))
        print("decoded_text:", decoded_text)
        print("decoded_text type:", type(decoded_text))
        print("logits type:", type(logits))
        print("logits length:", len(logits))
        print("first 5 logits:", logits[:5])
