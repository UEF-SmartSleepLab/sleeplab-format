from setuptools import find_packages, setup


def setup_package():
    setup(
        name = 'sleeplab_format',
        version = '0.1',
        author = 'Riku Huttunen',
        author_email = 'riku.huttunen@uef.fi',
        description = 'Tools for transforming heterogeneous source data to a unified format',
        license = 'MIT',
        packages = find_packages(include=[
            'sleeplab_format',
            'sleeplab_format.*',
            'profusion',
            'profusion.*'
        ]),
        install_requires = [
            'numpy',
            'pandas',
            'pyarrow',
            'pydantic',
            'pyedflib',
            'xmltodict'
        ],
        tests_require = [
            'pytest'
        ],
        python_requires = '>=3.10',
        entry_points = {
            'console_scripts': ['profusion_convert=profusion.convert:cli_convert_dataset']
        },
    )


if __name__ == '__main__':
    setup_package()