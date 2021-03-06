#!/usr/bin/env python
# -*- coding: latin-1 -*-
import codecs
import re
import os
from setuptools import setup


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return codecs.open(path, mode, encoding)


with open_local(['pyshacl_webservice', '__init__.py'], encoding='latin1')\
        as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

with open_local(['README.md']) as readme:
    long_description = readme.read()

with open_local(['requirements.txt']) as req:
    found_requirements = req.read().split("\n")
    dependency_links = []
    requirements = []
    for f in found_requirements:
        if f.startswith('#'):
            pass
        if 'git+' in f:
            pkg = f.split('#')[-1]
            dependency_links.append(f.strip() + '-9876543210')
            requirements.append(pkg.replace('egg=', '').rstrip())
        else:
            requirements.append(f.strip())

setup(
    name='pyshacl-webservice',
    packages=['pyshacl_webservice'],
    version=version,
    description='Python SHACL Validator as a Webservice',
    author='Ashley Sommer',
    author_email='ashley.sommer@csiro.au',
    url='https://github.com/RDFLib/pySHACL/',
    download_url='https://github.com/CSIRO-enviro-informatics/pyshacl-webservice/'
                    'archive/v{:s}.tar.gz'.format(version),
    license='LICENSE',
    keywords=['Linked Data', 'Semantic Web', 'Python',
              'SHACL', 'Shapes', 'Schema', 'Validate', 'Flask', 'Sanic'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Bug Reports':
            'https://github.com/CSIRO-enviro-informatics/pyshacl-webservice/issues',
        'Source': 'https://github.com/CSIRO-enviro-informatics/pyshacl-webservice/',
    },
    install_requires=requirements,
    dependency_links=dependency_links
)

