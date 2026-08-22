.PHONY: install run dev docker-up docker-down migrate lint typecheck

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --port 8080

dev:
	docker-compose up -d db
	@sleep 3
	uvicorn app.main:app --reload --port 8080

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head

lint:
	ruff check app/

typecheck:
	pyright app/
