# Makefile for AceTrack (macOS / Linux)

.PHONY: all backend frontend dev

backend:
	cd backend && source venv/bin/activate && uvicorn main:app --reload --port 10000

frontend:
	cd frontend && npm run dev

dev:
	npm run dev
