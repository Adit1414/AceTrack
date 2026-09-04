# Makefile for AceTrack (Windows)

.PHONY: all backend frontend dev

backend:
	cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 10000

frontend:
	cd frontend && npm run dev

dev:
	npm run dev
