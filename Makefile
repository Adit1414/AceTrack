# Makefile

.PHONY: all backend frontend dev

backend:
	cd backend && .\venv\Scripts\activate && uvicorn main:app --reload --port 10000



frontend:
	cd frontend && npm run dev

dev:
	cmd /c start cmd /k "make backend"
	cmd /c start cmd /k "make frontend"

