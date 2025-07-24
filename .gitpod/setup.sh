#!/bin/bash

set -e # エラーが発生した場合はスクリプトを終了

echo "🚀 Gitpod + Cursor + Cline 永続化セットアップを開始します..."

# --- VS Code Server 設定の永続化 ---
PERSISTENT_VSCODE_DIR="/workspace/agno/.vscode-server-data"
VSCODE_DIR="$HOME/.vscode-server"

echo "1. VS Code Server設定の永続化を確認・実行します。"
echo "   - 永続化ディレクトリ: $PERSISTENT_VSCODE_DIR"
echo "   - VS Codeディレクトリ: $VSCODE_DIR"

# 永続化ディレクトリが存在しない場合は作成
mkdir -p "$PERSISTENT_VSCODE_DIR/extensions"
mkdir -p "$PERSISTENT_VSCODE_DIR/data/Machine"

# シンボリックリンクが既に存在するか確認
if [ -L "$VSCODE_DIR" ]; then
    echo "✅ シンボリックリンクは既に設定済みです。スキップします。"
else
    echo "   - シンボリックリンクが存在しないため、設定処理を実行します。"
    # 元のディレクトリが存在する場合、中身を永続化ディレクトリに移動
    if [ -d "$VSCODE_DIR" ]; then
        echo "   - 既存の $VSCODE_DIR を $PERSISTENT_VSCODE_DIR に移動します..."
        # rsync を使って安全に移動・マージ
        rsync -a --remove-source-files "$VSCODE_DIR/" "$PERSISTENT_VSCODE_DIR/"
        rm -rf "$VSCODE_DIR"
        echo "   - 移動が完了しました。"
    fi
    
    # シンボリックリンクを作成
    echo "   - シンボリックリンクを作成します: $VSCODE_DIR -> $PERSISTENT_VSCODE_DIR"
    ln -s "$PERSISTENT_VSCODE_DIR" "$VSCODE_DIR"
    echo "   - シンボリックリンクを作成しました。"
fi
echo "✅ VS Code Server設定の永続化が完了しました。"
echo ""


# --- 拡張機能のインストール ---
echo "2. 必要なVS Code拡張機能をインストールします..."

# codeコマンドのパスを特定
if command -v code &> /dev/null; then
    CODE_CMD="code"
elif command -v /ide/bin/remote-cli/code &> /dev/null; then
    CODE_CMD="/ide/bin/remote-cli/code"
else
    echo "❌ codeコマンドが見つかりません。拡張機能のインストールをスキップします。"
    exit 1
fi

echo "   - 使用するコマンド: $CODE_CMD"

# Cline (Claude Dev) と Python 拡張機能をインストール
echo "   - saoudrizwan.claude-dev (Cline) をインストール中..."
$CODE_CMD --install-extension saoudrizwan.claude-dev --force
echo "   - ms-python.python をインストール中..."
$CODE_CMD --install-extension ms-python.python --force

echo "✅ 拡張機能のインストールが完了しました。"
echo ""


# --- SSH接続情報の準備 ---
echo "3. SSH接続情報を準備します..."

# SSH公開鍵をGitpodに登録
if [ -f ~/.ssh/id_rsa.pub ]; then
    gp ssh-public-key add "$(cat ~/.ssh/id_rsa.pub)" > /dev/null 2>&1 || echo "   - SSH公開鍵は既に登録済みです。"
fi

# SSH接続コマンドを生成
SSH_USER="gitpod"
SSH_HOST=$(gp url | sed 's|https://||' | sed 's|/|.ssh.gitpod.io|')
SSH_COMMAND="ssh $SSH_USER@$SSH_HOST"

# .bashrc にSSH接続情報を表示するエイリアスを追加
echo "   - 'cursor-ssh' コマンドを設定します。"
cat > "$HOME/.bashrc_cursor" &lt;&lt; 'EOF'
alias cursor-ssh='
echo "================================================================"
echo "📋 Cursor (SSH) 接続コマンド:"
echo "ssh gitpod@$(gp url | sed "s|https://||" | sed "s|/|.ssh.gitpod.io|")"
echo "================================================================"
'
EOF

# .bashrcに追記
if ! grep -q "source \$HOME/.bashrc_cursor" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# Load Cursor SSH alias" >> "$HOME/.bashrc"
    echo "source \$HOME/.bashrc_cursor" >> "$HOME/.bashrc"
fi

echo "✅ SSH接続情報の準備が完了しました。"
echo ""

echo "🎉 全てのセットアップが完了しました！"
echo "ワークスペース起動後、ターミナルで 'cursor-ssh' を実行して接続情報を確認してください。"
