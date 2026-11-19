#!/usr/bin/env bash
# Cria o ambiente virtual Python 3.14 e instala as dependências do projeto.
# Uso: ./scripts/setup_venv.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_VERSION="3.14"

echo "=== MatchCo - Setup do ambiente virtual ==="

# Localiza o Python 3.14
PYTHON_BIN=""

if command -v python3 &>/dev/null; then
  VERSION=$(python3 -c 'import sys; print(sys.version_info.major, sys.version_info.minor)')
  if [[ "$VERSION" == "3 14" ]]; then
    PYTHON_BIN=$(which python3)
  fi
fi

# Se não encontrou via python3, procura nos caminhos comuns do macOS
if [ -z "$PYTHON_BIN" ]; then
  CANDIDATES=(
    "/Library/Frameworks/Python.framework/Versions/$PYTHON_VERSION/bin/python3"
    "/usr/local/bin/python3.$PYTHON_VERSION"
    "/usr/bin/python3.$PYTHON_VERSION"
  )
  for candidate in "${CANDIDATES[@]}"; do
    if [ -x "$candidate" ]; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "ERRO: Python $PYTHON_VERSION não encontrado no sistema."
  echo "Instale o Python $PYTHON_VERSION em https://www.python.org/downloads/"
  exit 1
fi

echo "Python encontrado: $PYTHON_BIN"
"$PYTHON_BIN" --version

# Remove venv antigo se existir
if [ -d "$VENV_DIR" ]; then
  echo "Removendo ambiente virtual antigo..."
  rm -rf "$VENV_DIR"
fi

# Cria o ambiente virtual
echo "Criando ambiente virtual em $VENV_DIR..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

# Ativa e instala dependências
source "$VENV_DIR/bin/activate"
echo "Ambiente virtual ativado: $(python --version)"

echo "Atualizando pip..."
pip install --upgrade pip --quiet

echo "Instalando dependências do projeto..."
pip install -r "$PROJECT_ROOT/config/requirements.txt"

echo ""
echo "=== Setup concluído! ==="
echo "Para ativar o ambiente virtual, execute:"
echo "  source $VENV_DIR/bin/activate"
