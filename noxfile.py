import nox

nox.options.default_venv_backend = "venv"
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = [
    "3.9",
    "3.10",
    "3.11",
]


@nox.session(python=PYTHON_VERSIONS[0])
def lint(session):
    session.install(".[dev,test]")
    session.run("black", "--check", "src", "tests")
    session.run("isort", "--check", "src", "tests")
    session.run("mypy", "src")
    session.run("pylint", "src", "tests")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    session.install(".[test]")
    session.run(
        "pytest",
        "--cov=sns_batch_client",
        "tests",
    )