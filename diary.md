# Call Me Maybe Diary

## 2026-04-01

### 現時点の課題理解
- この課題の目的は、自然言語の prompt を構造化された function call JSON に変換する CLI ツールを作ること。
- 必須の起動方法は `uv run python -m src`。
- プログラムは関数定義ファイルと入力 prompt ファイルを読み込み、既定では `data/output/function_calling_results.json` に JSON 配列を書き出す。
- 各 prompt に対する出力オブジェクトは、次の3キーだけを必ず持つ必要がある。
  - `prompt`
  - `name`
  - `parameters`
- 実装は prompt の工夫だけに頼ってはいけず、`constrained decoding` を使う必要がある。
- 呼び出す関数の選択はヒューリスティクスではなく LLM が行う必要がある。
- 最終的な JSON ファイル全体は LLM に自由生成させず、意味的な要素を生成したあとに Python 側で組み立てるのが安全。

### 採用する実装方針
- `src` パッケージを作り、`__main__.py` を CLI のエントリポイントにする。
- 次の CLI 引数を受け取れるようにする。
  - `--functions_definition`
  - `--input`
  - `--output`
- 制約付きデコーディングは二段階で行う。
  1. 関数名 `name` を制約付きで生成する
  2. 選ばれた関数スキーマに従って `parameters` を制約付きで生成する
- 最終的な JSON オブジェクト列は Python 側で組み立てる。
- 不完全な output を出すよりも、明確なエラーメッセージを出して停止する方針を優先する。

### 課題文から見えている必須条件
- Python 3.10 以上
- flake8 に準拠したコード
- mypy を通せる型ヒント
- `pydantic` を使ったバリデーション
- 例外を適切に処理すること
- `llm_sdk` の private な属性やメソッドを使わないこと
- 関数選択をヒューリスティクスで行わないこと
- 提供された入力例に対するハードコードをしないこと
- 既定モデルは `Qwen/Qwen3-0.6B`

### 推奨する実装順
1. `src` パッケージの構成を作る
2. CLI の引数解析と既定パス処理を実装する
3. `pydantic` モデルを定義する
   - 関数定義
   - 入力 prompt
   - 出力オブジェクト
4. JSON 読み込みとバリデーションを実装する
5. `llm_sdk` の public API を使う薄いアダプタを作る
6. logits ベースの最小生成ループを作る
7. 関数名 `name` の制約付き生成を実装する
8. 型ごとのパラメータ値生成を実装する
9. Python 側で最終 JSON を組み立てて書き出す
10. 正常系、異常系、スキーマ整合性のテストを追加する

### 設計上の重要メモ
- この課題の本体は constrained decoding である。
- 最も安全な構成は以下。
  - LLM が `name` を決める
  - LLM が制約下で型付きパラメータ値を生成する
  - Python が検証して最終 JSON を組み立てる
- LLM に出力ファイル全体を自由生成させないこと。

### 全体ファイルツリー案
```text
call_me_maybe/
├── README.md
├── diary.md
├── pyproject.toml
├── uv.lock
├── llm_sdk/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── llm_sdk/
│       └── __init__.py
├── data/
│   ├── input/
│   │   ├── function_calling_tests.json
│   │   └── functions_definition.json
│   └── output/
│       └── function_calling_results.json
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── errors.py
│   ├── io_utils.py
│   ├── models.py
│   ├── prompt_builder.py
│   ├── llm_adapter.py
│   ├── decoder.py
│   ├── orchestrator.py
│   └── writer.py
├── tests/
│   ├── test_models.py
│   ├── test_io_utils.py
│   ├── test_decoder.py
│   └── test_orchestrator.py
└── Makefile
```

### 各ファイルの役割メモ
- `src/__main__.py`
  - `python -m src` の入口
- `src/cli.py`
  - 引数解析と既定値の管理
- `src/models.py`
  - `pydantic` モデル定義
- `src/io_utils.py`
  - JSON の読み込み、入力検証
- `src/llm_adapter.py`
  - `llm_sdk` の public API を使う薄いラッパ
- `src/prompt_builder.py`
  - 関数定義と prompt から LLM 入力を組み立てる
- `src/decoder.py`
  - 制約付きデコーダ本体
- `src/orchestrator.py`
  - 全体の進行制御
- `src/writer.py`
  - 最終 output JSON の書き出し
- `src/errors.py`
  - エラー型の整理
- `tests/`
  - ローカル検証用テスト
- `Makefile`
  - install / run / debug / clean / lint をまとめる

### 次にやるとよいこと
- まずは `src` のモジュール分割を紙や `diary.md` 上で固める
- その後に、`models.py` と `cli.py` から書き始める

### 現在の進捗メモ
- `src/` の基本ファイル群は作成済み
- `cli.py` では引数を受け取る方向まで進めた
- `__main__.py` から `cli.py` を呼ぶ入口は作成済み
- `models.py` はほぼ形になっている
  - `AppConfig`
  - `ParameterDefinition`
  - `FunctionDefinition`
  - `PromptItem`
  - `FunctionCallResult`
- `FunctionDefinition.parameters` は `dict[str, ParameterDefinition]` で持つ方向を確認済み
- `ParameterDefinition.type` が `str` である理由を理解した
- `json_loader.py` を作り始めた
  - `json.load()` を使う方向へ修正済み
  - `FunctionDefinition(**item)` と `PromptItem(**item)` でインスタンス化する流れを確認済み
- 現時点の `json_loader.py` で残っている主な修正点
  - 不要 import を消す
  - `read_json_file` の返り値型を見直す
  - 崩れたコメントを整理する

### 今の段階での理解メモ
- `argparse` は CLI 引数の受付係
- `python -m src` の `-m` は `src/__main__.py` を入口にするための仕組み
- `json.load()` は JSON ファイルを Python の `list` や `dict` に変換する
- `**item` は辞書をキーワード引数として展開する書き方
- `FunctionDefinition(**item)` もちゃんとインスタンス生成である
- 今回の入力は「行ベースの手書きパース」ではなく「構造化 JSON をそのままモデル化する」方式が自然

## 2026-04-08

### 今日確認できたこと
- `uv run python -m src` は通り、現状の `orchestrator.py` では関数定義 5 件、prompt 11 件を読み込めることを確認した
- `src/llm_adapter.py` で `llm_sdk` の public API を直接触る実験を行った
- import は `from llm_sdk import Small_LLM_Model` で通ることを確認した
- `build_model()` により `Qwen/Qwen3-0.6B` を実際にダウンロードして初期化できた
- `encode_text()` の結果は `torch.Tensor` ではなく `list[int]` に直して返す形に修正した
- `decode_tokens()` で token ids から元の文字列に戻せることを確認した
- `get_next_token_logits()` を追加し、次 token 用 logits が `list[float]` として取得できることを確認した
- 実験では `What is the sum of 2 and 3?` を入力し、token ids、復元文字列、logits の長さを確認できた

### 今日理解が深まったこと
- token は「文字そのもの」でも「単語そのもの」でもなく、tokenizer が作る文章の部品である
- 同じ tokenizer なら同じ token には同じ id が割り当てられるが、`hello` が常に 1 token になるとは限らない
- `tensor` は機械学習向けの数値コンテナであり、今回の decoder 実装では Python の `list[int]` に変換した方が扱いやすい
- logits は「全文の答え」ではなく「次の 1 token 候補すべての生スコア一覧」である
- constrained decoding では、logits を見た上で「候補として許可される token だけ残す」必要がある

### decoder.py で見えてきた方針
- `is_valid_prefix(generated, candidates)` で、生成途中文字列が関数名候補の prefix として有効かを判定する方向は良さそう
- 関数名生成時の `candidates` は `functions_definition.json` に含まれる全関数名の一覧になる
- `choose_token()` は 1 回で文字列全体を決める関数ではなく、「次の 1 token」を決める関数として何度も呼ばれる想定
- 今の `choose_token()` にはまだ生成ループ本体がなく、`token_texts` をどう用意するかも未解決
- invalid な token しかない場合は `-1` を返すより `DecodeError` にした方が安全

### 現在地の整理
- CLI と JSON 読み込みの土台はある
- LLM 接続の最小実験は通った
- ただし mandatory part の本体である constrained decoding はまだ骨格段階
- `decoder.py` は prefix 判定と最高 score 選択の発想までは入ったが、まだ end-to-end では動かない
- `prompt_builder.py`、`writer.py`、各種テストは未着手に近い

### 次にやること
- `decoder.py` に「logits を取る -> valid token を絞る -> 1 token 追加する」を回す最小ループを書く
- 関数名 candidate 一覧を `orchestrator.py` か decoder 呼び出し側で作る
- `token_texts` をどう作るかを整理する
- 関数名だけでも constrained decoding で 1 件通す
- その後に `prompt_builder.py` と `writer.py` をつなぐ

## 提出までのチェックリスト

以下のチェックがすべて埋まれば、mandatory part の提出準備が整う想定。

### 1. プロジェクト土台
- [x] ルートに `pyproject.toml` を用意した
- [x] ルートに `uv.lock` を用意した
- [x] ルートに `Makefile` を用意した
- [x] `Makefile` に `install`, `run`, `debug`, `clean`, `lint` がある
- [x] `src/` ディレクトリを作成した
- [x] `src/__init__.py` を作成した
- [x] `src/__main__.py` を作成した
- [x] `llm_sdk/` を同階層に置いた
- [x] `.gitignore` に Python の不要物を含めた
- [x] `data/input/` の読み込み前提を確認した
- [x] `data/output/` は生成対象であり、repo に含めない方針を確認した

### 2. CLI 入口
- [x] `python -m src` で起動する構成にした
- [x] `--functions_definition` を受け取れる
- [x] `--input` を受け取れる
- [x] `--output` を受け取れる
- [x] 引数未指定時の既定パスを設定した
- [x] CLI からオーケストレータを呼び出せる
- [ ] 例外発生時にわかりやすいエラーを出せる

### 3. 入力データモデル
- [x] `FunctionDefinition` モデルを作成した
- [x] `FunctionParameter` モデルを作成した
- [x] `PromptItem` モデルを作成した
- [x] `FunctionCallResult` モデルを作成した
- [x] `AppConfig` など設定モデルを作成した
- [x] すべて `pydantic` でバリデーションする
- [x] 型ヒントを付けた
- [ ] docstring を書いた

### 4. 入力読み込みと検証
- [x] 関数定義 JSON を読み込める
- [x] prompt 入力 JSON を読み込める
- [x] JSON パース失敗時に明確なエラーを出せる
- [x] ファイル欠如時に明確なエラーを出せる
- [ ] 必須キー欠如時に明確なエラーを出せる
- [ ] 未対応の parameter type を検知できる
- [ ] 関数定義一覧を名前で引ける形に整理できる

### 5. LLM 接続
- [x] `llm_sdk` の public API だけを使っている
- [x] `Small_LLM_Model` を起動できる
- [x] prompt を token ids に変換できる
- [x] token ids から logits を取得できる
- [x] 必要なら token ids を文字列に戻せる
- [ ] vocab か tokenizer 情報を取得できる
- [ ] モデル初期化失敗時に明確なエラーを出せる

### 6. プロンプト構築
- [ ] 関数定義一覧を LLM に渡す入力形式を決めた
- [ ] 1件の prompt に対する入力文を組み立てられる
- [ ] `name` 生成用の文脈を作れる
- [ ] `parameters` 生成用の文脈を作れる
- [ ] prompt のみで正解を誘導する設計に依存していない

### 7. 制約付きデコーダ基盤
- [ ] logits を受け取って次 token 候補を選ぶループを書いた
- [ ] 「いま許される token 集合」を計算する仕組みを作った
- [ ] 無効 token を除外できる
- [ ] token を1つずつ追加して状態遷移できる
- [ ] 生成終了条件を定義した
- [ ] 生成失敗時のエラー処理を入れた

### 8. 関数名 `name` の制約付き生成
- [x] 許可される関数名候補を列挙できる
- [ ] 候補の prefix に基づいて token を制約できる
- [ ] 最終的に候補のどれか1つへ確定できる
- [ ] 存在しない関数名が出ないことを保証できる
- [ ] 曖昧な prompt でも候補内から選ばせる仕組みになっている

### 9. `parameters` の制約付き生成
- [ ] 選ばれた関数の parameter schema を取得できる
- [ ] `string` 型を制約付きで生成できる
- [ ] `number` 型を制約付きで生成できる
- [ ] `boolean` 型を制約付きで生成できる
- [ ] 複数引数関数を処理できる
- [ ] 必須引数をすべて埋められる
- [ ] 不要な引数を出さないようにできる
- [ ] 型が一致しない値を拒否できる

### 10. 出力組み立て
- [ ] 各 prompt ごとに `prompt`, `name`, `parameters` を Python 側で組み立てる
- [ ] 余計なキーを含めない
- [ ] 結果を配列として蓄積できる
- [ ] 全件分の結果を1つの JSON 配列にできる
- [ ] 出力順を入力順に保てる

### 11. 出力検証と保存
- [ ] 出力オブジェクトを保存前に再検証できる
- [ ] `name` が関数定義内に存在することを確認できる
- [ ] `parameters` のキーが定義と一致することを確認できる
- [ ] `parameters` の型が定義と一致することを確認できる
- [ ] valid JSON として保存できる
- [ ] `--output` で指定したパスに保存できる
- [ ] 既定では `data/output/function_calling_results.json` に保存できる

### 12. エラー処理
- [ ] 想定される失敗を例外クラスで整理した
- [ ] ユーザー向けエラーメッセージを統一した
- [ ] 異常終了時に壊れた output を残さない
- [ ] 未処理例外でクラッシュしない
- [ ] レビュー中に起きそうな入力ミスにも対応した

### 13. ローカル検証
- [x] デフォルトパスで実行確認した
- [ ] カスタムパスで実行確認した
- [ ] 提供された input で JSON が生成されることを確認した
- [ ] 出力が schema に一致することを確認した
- [ ] 空文字列ケースを試した
- [ ] 大きい数のケースを試した
- [ ] 特殊文字のケースを試した
- [ ] 複数引数関数のケースを試した
- [ ] 壊れた JSON 入力のケースを試した
- [ ] 欠損ファイルのケースを試した

### 14. 品質チェック
- [ ] `flake8 .` を通した
- [ ] `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs` を通した
- [ ] 関数とクラスに必要な docstring を書いた
- [ ] 命名を見直した
- [ ] 説明できない処理が残っていない

### 15. README
- [ ] README を英語で書いた
- [ ] 1行目を課題指定の italic 文にした
- [ ] Description セクションを書いた
- [ ] Instructions セクションを書いた
- [ ] Resources セクションを書いた
- [ ] AI をどう使ったかを明記した
- [ ] constrained decoding の説明を書いた
- [ ] 設計判断を書いた
- [ ] 性能面の分析を書いた
- [ ] 苦労した点を書いた
- [ ] テスト戦略を書いた
- [ ] 実行例を書いた

### 16. 最終提出前確認
- [ ] repo に `src/` がある
- [ ] repo に `pyproject.toml` がある
- [ ] repo に `uv.lock` がある
- [ ] repo に `llm_sdk/` がある
- [ ] repo に `data/input/` がある
- [ ] repo に README がある
- [ ] `output/` を commit していない
- [ ] `uv sync` 前提で動くことを確認した
- [x] `uv run python -m src` で起動確認した
- [ ] 出力 JSON が mandatory part の仕様を満たしている

## 実装タスク分解

### A. 最初に作るファイル
- [x] `src/__init__.py`
- [x] `src/__main__.py`
- [x] `src/cli.py`
- [x] `src/models.py`
- [ ] `src/io_utils.py`
- [ ] `src/errors.py`
- [ ] `src/llm_adapter.py`
- [ ] `src/prompt_builder.py`
- [ ] `src/decoder.py`
- [ ] `src/orchestrator.py`
- [ ] `src/writer.py`
- [ ] `tests/`
- [ ] `Makefile`
- [x] ルート `pyproject.toml`

### B. 先に終わらせるべき順番
1. [x] `pyproject.toml`, `src/`, `__main__.py`, `cli.py` を作る
2. [ ] `models.py`, `io_utils.py`, `errors.py` を作る
3. [ ] 入力読み込みと validation を完成させる
4. [ ] `llm_adapter.py` を作る
5. [ ] `prompt_builder.py` を作る
6. [ ] `decoder.py` に name 生成を実装する
7. [ ] `decoder.py` に parameter 生成を実装する
8. [ ] `orchestrator.py` で全体をつなぐ
9. [ ] `writer.py` で output 保存を実装する
10. [ ] tests と lint を通す
11. [ ] README を完成させる
12. [ ] 提出前確認を全部埋める

memo
