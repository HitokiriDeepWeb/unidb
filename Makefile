# Run all tests.
test:
	pytest

unit:
	pytest src/tests/unit

integration:
	pytest src/tests/integration
