#!/bin/bash

set -e

echo ""
echo "========================================"
echo "       AniVora AI Engine Setup"
echo "========================================"
echo ""

if command -v ollama >/dev/null 2>&1; then
    echo "Ollama is already installed."
else
    echo "Installing Ollama..."

    curl -fsSL https://ollama.com/install.sh | sh
fi

echo ""
echo "Starting Ollama..."

if pgrep -x ollama >/dev/null 2>&1; then
    echo "Ollama is already running."
else
    nohup ollama serve > ollama.log 2>&1 &
    sleep 5
fi

echo ""
echo "Downloading AniVora AI model..."

ollama pull "${ANIVORA_AI_MODEL:-llama3.2}"

echo ""
echo "========================================"
echo "       AI Engine Ready"
echo "========================================"
echo ""
echo "Model: ${ANIVORA_AI_MODEL:-llama3.2}"
echo "URL:   ${ANIVORA_AI_URL:-http://127.0.0.1:11434}"
echo ""
