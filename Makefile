# Makefile
.PHONY: help up down logs restart clean build shell test

help:
	@echo "Available commands:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs"
	@echo "  make restart   - Restart all services"
	@echo "  make clean     - Clean up everything"
	@echo "  make build     - Rebuild images"
	@echo "  make shell     - Shell into backend"
	@echo "  make test      - Run tests"

up:
	docker-compose up --build -d
	@echo "✅ Services started! Check http://localhost:3000"

down:
	docker-compose down

logs:
	docker-compose logs -f --tail=100

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f
	rm -rf uploads/* temp/*

build:
	docker-compose build --no-cache

shell:
	docker-compose exec backend /bin/bash

test:
	docker-compose exec backend python -m pytest

# Production commands
prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f