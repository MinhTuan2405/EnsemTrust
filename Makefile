up:
	docker compose up -d

down:
	docker compose down -v

build:
	docker compose build

restart:
	make down && make up

build_run_all:
	docker compose up -d --build

upload:
	powershell -ExecutionPolicy Bypass -File ./git_upload.ps1
