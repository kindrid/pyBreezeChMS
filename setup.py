#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    long_description = readme.read()


setup(
    name='txBreezeChMS',
    version='1.0.3',
    description="Twisted Python interface to BreezeChMS REST API.",
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
    ],
    keywords='breezechms breezeapi twisted python breeze',
    author='Trenton Broughton',
    author_email='engineering@kindrid.com',
    maintainer='Trenton Broughton',
    maintainer_email='engineering@kindrid.com',
    url='http://www.github.com/aortiz32/pyBreezeChMS/',
    license='Apache 2.0',
    packages=['txbreeze'],
    install_requires=['treq'],
    zip_safe=False,
)
