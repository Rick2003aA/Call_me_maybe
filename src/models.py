from pydantic import BaseModel


class AppConfig(BaseModel):
    functions_definition: str
    input: str
    output: str


class ParameterDefinition(BaseModel):
    """
    引数の型を記録する
    """
    type: str


class FunctionDefinition(BaseModel):
    """
    関数の定義を記録する
     - name: 関数の名前
     - description: 関数の説明
     - parameters: 引数の定義
    """
    name: str
    description: str
    parameters: dict[str, ParameterDefinition]
    returns: ParameterDefinition


class PromptItem(BaseModel):
    prompt: str


class FunctionCallResult(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, object]
