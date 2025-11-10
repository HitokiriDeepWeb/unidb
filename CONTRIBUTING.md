# How to contribute

## Dependencies

[`uv`](https://docs.astral.sh/uv/) is used to manage the dependencies.

To install them you would need to run install command:
`uv sync`

To activate your virtualenv run `source .venv/bin/activate`.

## Tests

To run all tests:
`make test`

To run unit tests:
`make unit`

To run integration tests:
`make integration`

## Submitting your code

The protected main branch is used, so the only way to push your code is via pull request.
To implement a new feature or to fix a bug create a new branch with the bug or feature name in it.
Then create a pull request to main branch

## Before submitting

Before submitting your code please do the following steps:

1. Run `make test` to make sure everything was working before.
2. Add any changes you want.
3. Add tests for the new changes.
4. Edit documentation if you have changed something significant.
5. Run `make test` again to make sure it is still working.

**The owner of this repository may refactor the code so it will match the general style. And change it any possible way.**

## Other help

You can contribute by spreading a word about this utility.
