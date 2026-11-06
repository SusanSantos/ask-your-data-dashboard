.PHONY: install run test lint
install:
	pip install -r requirements.txt
run:
	PYTHONPATH=. streamlit run src/app.py
test:
	pytest -q
lint:
	ruff check .
