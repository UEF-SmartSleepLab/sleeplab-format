# sleeplab-format

**NOTE: this software is under initial development, breaking changes may occur.**

Tools for transforming heterogeneous sleep measurement data to a unified format.

## Installation

For development, you need to [install from cloned repository](#install-from-cloned-repository). To just use the current version, [install with pip from github](#install-with-pip-from-github).

### Install with pip from Github

```bash
pip install git+https://github.com/UEF-SmartSleepLab/sleeplab-format.git#egg=sleeplab-format
```

### Install from cloned repository

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

## How to contribute

We follow [Github flow](https://docs.github.com/en/get-started/quickstart/github-flow) in the development. 

The basic procedure to contribute code to the project is:

1. [Install from cloned repository](#install-from-cloned-repository)
2. Create your own branch and implement the changes (and tests, preferably)
3. [Make sure the tests pass](#running-tests)
4. Create a pull request on Github
5. Another contributor reviews the pull request
6. Fix review comments if any
7. Reviewer merges the pull request
