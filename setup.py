import re

from setuptools import setup

with open('requirements.txt') as req_file:
    deps = req_file.read().splitlines()

# Single source of truth for the version, without importing the package (and its dependencies) at build time.
with open('dftest/__init__.py') as init_file:
    version = re.search(r"^__version__ = '([^']+)'", init_file.read(), re.M).group(1)

with open('README.md') as readme_file:
    long_description = readme_file.read()

setup(
    name='dftest',
    packages=['dftest'],
    version=version,
    scripts=['bin/dftest'],
    install_requires=deps,
    python_requires='>=3.10',
    description='A library for testing and analyzing data integrity.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Atai Ambus & Ran Gilad-Bachrach',
    license='MIT'
)
