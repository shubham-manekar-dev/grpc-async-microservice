.PHONY: format lint test backend-test frontend-test integration-test shellcheck java-test mct smoke ci grpc-codegen topology docker-up docker-down docker-logs

format:
	@echo "Format hooks are handled by editors in this POC"

lint:
	@echo "Add static analysis tools (ruff, mypy) as needed"

test: backend-test frontend-test integration-test java-test shellcheck mct

backend-test:
	cd backend && pytest -m "not integration"

frontend-test:
	cd frontend && npm run build && npm test -- --run

integration-test:
	cd backend && pytest -m integration

shellcheck:
	@files=$$(git ls-files '*.sh'); \
	if ! command -v shellcheck >/dev/null 2>&1; then \
		echo "ShellCheck not installed, skipping"; \
	elif [ -n "$$files" ]; then \
		shellcheck $$files; \
	else \
		echo "No shell scripts detected, skipping"; \
	fi

java-test:
	mvn -f java-tests/pom.xml test

mct:
	./scripts/mct.py

smoke:
	./scripts/ci_smoke.sh

ci:
	$(MAKE) backend-test
	$(MAKE) frontend-test
	$(MAKE) integration-test
	$(MAKE) shellcheck
	$(MAKE) java-test
	$(MAKE) mct
	$(MAKE) smoke

grpc-codegen:
	python scripts/codegen_grpc.py

topology:
	python docs/render_topology.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
