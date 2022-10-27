from setuptools import find_packages, setup


def setup_package():
    setup(
        name = 'dataset_generation',
        version = '0.0.1',
        author = 'Riku Huttunen',
        author_email = 'riku.huttunen@uef.fi',
        description = 'Tools for transforming heterogeneous source data to a unified format',
        license = 'MIT',
        packages = find_packages(include=[
            'dataset_generation', 'dataset_generation.*'
        ]),
        install_requires = [
            'numpy',
            'pydantic',
            'pyedflib'
        ],
        python_requires = '>=3.10'
    )


if __name__ == '__main__':
    setup_package()