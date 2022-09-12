#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst', encoding="utf8") as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst', encoding="utf8") as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Frederique de Groen, Kees van Ginkel, Margreet van Marle, Amine Aboufirass",
    author_email='Margreet.vanMarle@deltares.nl',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Risk Assessment  and Adaptation for Critical infrastructurE.",
    entry_points={
        'console_scripts': [
            'ra2ce=ra2ce.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='ra2ce',
    name='ra2ce',
    packages=find_packages(include=['ra2ce', 'ra2ce.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/Deltares/ra2ce',
    version='0.0.1',
    zip_safe=False,
)
