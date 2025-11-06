# Run all tests.
run_tests:
	pytest

# Run unit tests.
run_unit_tests:
	pytest src/tests/unit

# Run integration tests.
run_integration_tests:
	pytest src/tests/integration
