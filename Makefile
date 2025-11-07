# Run all tests.
run_tests:
	pytest

run_unit_tests:
	pytest src/tests/unit

run_integration_tests:
	pytest src/tests/integration
