.PHONY: migrate migrate-down migrate-revision run

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-revision:
	alembic revision --autogenerate -m "$(msg)"

run:
	uvicorn app.main:app --reload --port 8001
