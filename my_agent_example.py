"""AGNO フレームワークを使った日本語エージェントの例

このプログラムは、AGNOフレームワークを使用して、
ユーザーの質問に対して親切に答える日本語のAIエージェントを実装します。

Gitpod環境での実行方法:
1. /workspace/agno/libs/agno ディレクトリで `pip install -e .` を実行 (完了済み)
2. `pip install anthropic` を実行 (完了済み)
3. .envファイルに ANTHROPIC_API_KEY を設定
4. python my_agent_example.py を実行
"""

import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

from agno.agent import Agent
from agno.models.anthropic import Claude

# 日本語の親切なアシスタントエージェントを作成
assistant_agent = Agent(
    name="日本語アシスタント",
    model=Claude(id="claude-sonnet-4-20250514"),
    instructions=[
        "あなたは親切で知識豊富な日本語のアシスタントです。",
        "ユーザーの質問に対して、分かりやすく丁寧に回答してください。",
        "回答は適切に構造化し、必要に応じて箇条書きや番号付きリストを使用してください。",
        "ユーザーのレベルに合わせて説明の詳しさを調整してください。",
        "親しみやすい口調で話しかけ、時には絵文字も使って温かみのある対話を心がけてください。"
    ],
    markdown=True,
    add_datetime_to_instructions=True,
    add_location_to_instructions=True,
)

# ツール付きのエージェントの例
from agno.tools.duckduckgo import DuckDuckGoTools

research_agent = Agent(
    name="リサーチアシスタント",
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "あなたは優秀なリサーチアシスタントです。",
        "最新の情報を検索して、正確で信頼性の高い情報を提供してください。",
        "検索結果は出典を明記し、日本語で分かりやすくまとめてください。",
        "情報の信頼性を評価し、複数の情報源を比較検討してください。"
    ],
    show_tool_calls=True,
    markdown=True,
)

# メモリ機能付きのエージェントの例
from agno.memory.v2.memory import Memory

memory_agent = Agent(
    name="メモリー付きアシスタント",
    model=Claude(id="claude-sonnet-4-20250514"),
    memory=Memory(),
    instructions=[
        "あなたは記憶力の良いアシスタントです。",
        "ユーザーとの過去の会話を覚えており、文脈に応じて適切に参照してください。",
        "ユーザーの好みや重要な情報を記憶し、パーソナライズされた対応を心がけてください。"
    ],
    enable_user_memories=True,
    enable_session_summaries=True,
    add_history_to_messages=True,
    num_history_runs=5,
    markdown=True,
)

# 推論機能付きのエージェントの例
reasoning_agent = Agent(
    name="推論エージェント",
    model=Claude(id="claude-sonnet-4-20250514"),
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=5,
    instructions=[
        "複雑な問題に対しては、段階的に考えて解決策を導き出してください。",
        "推論プロセスを明確に示し、各ステップでの判断根拠を説明してください。",
        "最終的な結論に至るまでの思考過程を透明化してください。"
    ],
    markdown=True,
)

# チームエージェントの例
web_agent = Agent(
    name="ウェブ検索担当",
    role="最新の情報をウェブから検索します",
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[DuckDuckGoTools()],
    instructions=["検索結果を日本語でまとめてください"],
    show_tool_calls=True,
)

analysis_agent = Agent(
    name="分析担当",
    role="情報を分析し、洞察を提供します",
    model=Claude(id="claude-sonnet-4-20250514"),
    instructions=["データを分析し、重要なポイントを抽出してください"],
)

from agno.team import Team

team = Team(
    name="リサーチチーム",
    members=[web_agent, analysis_agent],
    model=Claude(id="claude-sonnet-4-20250514"),
    instructions=[
        "チームメンバーと協力して、包括的な調査結果を提供してください",
        "各メンバーの専門性を活かして、最高の結果を出してください"
    ],
    markdown=True,
)

# 使用例
if __name__ == "__main__":
    print("=== 基本的なアシスタントの例 ===")
    assistant_agent.print_response("AGNOフレームワークについて教えてください", stream=True)
    
    print("\n=== リサーチエージェントの例 ===")
    # research_agent.print_response("最新のAI技術のトレンドについて調べてください", stream=True)
    
    print("\n=== 推論エージェントの例 ===")
    # reasoning_agent.print_response(
    #     "もし地球の自転が突然止まったらどうなるか、科学的に説明してください",
    #     stream=True,
    #     show_full_reasoning=True
    # )
    
    # インタラクティブモード
    # assistant_agent.cli_app(
    #     user="ユーザー",
    #     emoji="👤",
    #     markdown=True,
    #     exit_on=["終了", "exit", "quit"]
    # )
