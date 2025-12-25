#!/usr/bin/env sh
set -e

python -m vsuet_accounting.infrastructure.db.bootstrap
exec streamlit run src/vsuet_accounting/app.py --server.port=8501 --server.address=0.0.0.0
