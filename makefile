.PHONY: migrate migrate-down migrate-revision

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-revision:
	alembic revision --autogenerate -m "$(msg)"
