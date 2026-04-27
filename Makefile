.PHONY: setup dev backend frontend eval test clean

setup:
	cd backend && uv sync
	cd frontend && npm install

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend' and 'make frontend' in two terminals"

eval:
	cd backend && uv run python -m eval.run_eval

test:
	cd backend && uv run pytest

clean:
	rm -rf backend/.venv frontend/node_modules frontend/.next
