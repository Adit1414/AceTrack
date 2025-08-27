# Makefile

.PHONY: all backend frontend dev

backend:
	cd backend && uvicorn backend.app.main:app --reload


frontend:
	cd frontend && npm run dev

dev:
	cmd /c start cmd /k "make backend"
	cmd /c start cmd /k "make frontend"

