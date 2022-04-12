import sys
from os import path

from setuptools import find_packages, setup

if sys.version_info < (3, 7, 0):
    raise OSError(
        f'hubble-python-client requires Python >=3.7, but yours is {sys.version}'
    )

try:
    pkg_name = 'hubble-python-client'
    libinfo_py = path.join(
        path.dirname(__file__), pkg_name.replace('-', '_'), '__init__.py'
    )
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][
        0
    ]
    exec(version_line)  # gives __version__
except FileNotFoundError as ex:
    __version__ = '0.0.0'

try:
    with open('./README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

setup(
    name=pkg_name,
    packages=find_packages(),
    version=__version__,
    include_package_data=True,
    description='Jina Hubble API Python SDK',
    author='Jina AI',
    author_email='hello@jina.ai',
    license='Apache 2.0',
    url='https://github.com/jina-ai/hubble-client-python',
    download_url='https://github.com/jina-ai/hubble-client-python/tags',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    setup_requires=['setuptools>=18.0', 'wheel'],
    install_requires=['requests>=2.27.1'],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'black',
            'isort',
            'flake8',
            'click',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Source': 'https://github.com/jina-ai/hubble-python-client/',
        'Tracker': 'https://github.com/jina-ai/hubble-python-client/issues',
    },
    keywords='jina hubble api sdk python client',
)
