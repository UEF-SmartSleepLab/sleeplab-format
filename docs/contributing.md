# Contributing

We follow [Github flow](https://docs.github.com/en/get-started/quickstart/github-flow) in the development. 

The basic procedure to contribute code to the project is:

1. [Install from cloned repository](#install-from-cloned-repository)
2. Create your own branch and implement the changes (and tests, preferably)
3. [Make sure the tests pass](#running-tests)
4. Create a pull request on Github
5. Another contributor reviews the pull request
6. Fix review comments if any
7. Reviewer merges the pull request

## Install from cloned repository

Clone repository to your local files:
```bash
git clone git@github.com:UEF-SmartSleepLab/sleeplab-format.git
```

This project uses [Hatch](https://hatch.pypa.io/latest/) for project management. First, [install hatch](https://hatch.pypa.io/latest/install/). You will also need a recent version of pip.

Then, go to the root of the cloned repository and create an environment for it:
```bash
hatch env create
```

After that, you can enter the environment by:
```bash
hatch shell
```

You can confirm that the project has been installed by:
```bash
pip show sleeplab-format
```

## Running tests

This project uses `pytest` for testing. To run the tests after cloning and installing, go to the root of the cloned repository and run:
```bash
pytest
```

## Documenting the source code

The source code should be documented using [Google style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

## Generating the documentation

This documentation is created using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and [mkdocstrings](https://mkdocstrings.github.io/). The documentation is published using [Github Pages](https://pages.github.com/). There are utility scripts defined in `pyproject.toml` to build and publish the documentation.

When working on documentation, use hatch environment `docs`:
```console
hatch -e docs shell
```

Build the documentation:
```console
hatch run docs:build
```

Serve the documentation on local machine for inspection:
```console
hatch run docs:serve
```

Publish the documentation:
```console
hatch run docs:publish
```

## Publishing to Zenodo

Whenever a new release is created in Github, the version will automatically be published in Zenodo.

## Publishing to PyPI

First, **remember to update the version in version.py**. Then, follow [Hatch publishing instructions](https://hatch.pypa.io/1.9/publish/). 

Build the package with hatch:
```bash
hatch build
```

Then, publish to TestPyPI with:
```bash
hatch publish -r test
```

If the TestPyPI package is OK, publish to PyPI with:
```bash
hatch publish
```

Use [token authentication](https://pypi.org/help/#apitoken) with PyPI.
