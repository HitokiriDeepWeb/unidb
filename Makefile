# Run all tests.
tests:
	pytest

unit:
	pytest src/tests/unit

integration:
	pytest src/tests/integration
