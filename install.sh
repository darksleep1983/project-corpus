#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
LANGUAGE="en"
PROJECT_HOME=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --language)
      [ "$#" -ge 2 ] || { echo "--language requires en or ru" >&2; exit 2; }
      LANGUAGE="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: ./install.sh /absolute/path/to/project-home [--language en|ru]"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
    *)
      [ -z "$PROJECT_HOME" ] || { echo "Only one project-home path is allowed" >&2; exit 2; }
      PROJECT_HOME="$1"
      shift
      ;;
  esac
done

[ -n "$PROJECT_HOME" ] || { echo "Usage: ./install.sh /absolute/path/to/project-home [--language en|ru]" >&2; exit 2; }
case "$LANGUAGE" in en|ru) ;; *) echo "--language must be en or ru" >&2; exit 2;; esac
if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  if [ "$LANGUAGE" = "ru" ]; then
    echo "Нужен Python 3.11 или новее." >&2
  else
    echo "Python 3.11 or newer is required." >&2
  fi
  exit 1
fi
[ "$LANGUAGE" = "ru" ] && READY="Project Corpus готов:" || READY="Project Corpus ready:"
[ -d "$REPO_ROOT/.venv" ] || "$PYTHON" -m venv "$REPO_ROOT/.venv"
"$REPO_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$REPO_ROOT/.venv/bin/python" -m pip install -e "$REPO_ROOT"
"$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/setup_project.py" \
  --project-home "$PROJECT_HOME" --repo-root "$REPO_ROOT" --language "$LANGUAGE"
echo "$READY $PROJECT_HOME/Corpus"
[ "$LANGUAGE" = "ru" ] && echo "Запустите сервер: ./start.sh" || echo "Start the server: ./start.sh"
