import json

from .errors import OutputFileError
from .models import FunctionCallResult


def write_results(output_path: str, results: list[FunctionCallResult]) -> None:
    """結果一覧を JSON 配列としてファイルに書き出す。"""
    payload = [result.model_dump() for result in results]

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
    except OSError as error:
        raise OutputFileError(
            f"Failed to write output file: {output_path}"
        ) from error
