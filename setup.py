from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
import os
from subprocess import check_call
from sys import platform


"""with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []
with open('requirements.txt') as rqmts:
    for r in rqmts:
        requirements.append(r.strip('\n'))"""


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        # own code
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # own code
        install.run(self)


setup(
    name='quickndirtybot',
    version="0.0.1",
    description="a quick and dirty crypto trading bot",
    long_description="a quick and dirty crypto trading bot",
    author="Heinrich Grabmayr",
    author_email="",
    # url='https://github.com/ericmjl/nxviz',
    entry_points={'console_scripts':
                  ['quickndirtybot = quickndirtybot.__main__:main']},
    packages=[
        'quickndirtybot',
    ],
    package_dir={'quickndirtybot': 'quickndirtybot'},
    include_package_data=True,
    # install_requires=requirements,
    license="MIT license",
    keywords='quickndirtybot',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
    cmdclass={
            'develop': PostDevelopCommand,
            'install': PostInstallCommand}
)
