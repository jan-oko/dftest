import os

from setuptools import setup

with open('requirements.txt') as req_file:
    deps = req_file.readlines()

#if 'COLAB_GPU' not in os.environ:
#    deps.append('pandasgui')

setup(
    name='dftest',
    packages=['dftest'],
    version='0.5.4',
    scripts=['bin/dftest'],
    install_requires=deps,
    description='A library for testing and analyzing data integrity.',
    author='Atai Ambus & Ran Gilad-Bachrach',
    license='MIT'
)
