up:
	docker compose up -d --wait

down:
	docker compose down

clean:
	docker compose down -v --remove-orphans

lint:
	poetry run ruff check --fix && poetry run ruff format .

test:
	poetry run pytest