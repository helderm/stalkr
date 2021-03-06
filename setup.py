#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

def get_requirements(file_name='requirements.txt'):
    try:
        filename = open(file_name)
        lines = [i.strip() for i in filename.readlines()]
        filename.close()
    except:
        return []

    return lines


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ''

requirements = get_requirements()

test_requirements = []

setup(
    name='stalkr',
    version='0.1.0',
    description="An user recommender app powered by Twitter",
    long_description=readme + '\n\n' + history,
    author="Helder Martins",
    author_email='heldergaray@gmail.com',
    url='https://github.com/helderm/stalkr',
    packages=[
        'stalkr',
    ],
    package_dir={'stalkr':
                 'stalkr'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='stalkr',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
