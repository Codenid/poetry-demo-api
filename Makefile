export:
	poetry export -f requirements.txt --without-hashes > requirements.txt

build:
	docker build -t poetry-demo .

audit:
	python audit_deps/audit.py

compose:
	docker compose up -d --build

clean:
	rm -f requirements.txt

size:
	docker image ls | grep fastapi_poetry_i
	docker history fastapi_poetry_i

layers:
	docker history fastapi_poetry_i --no-trunc > layers.txt