# Makefile

.PHONY: all backend frontend dev

backend:
	cd src && uvicorn backend.main:app --reload


frontend:
	npm run dev

dev:
	cmd /c start cmd /k "make backend"
	cmd /c start cmd /k "make frontend"

