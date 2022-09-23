from setuptools import find_packages, setup

# package metadata
_description = 'SDK for Hubble API at Jina AI.'
_setup_requires = ['setuptools>=18.0', 'wheel']
_python_requires = '>=3.7.0'
_author = 'Jina AI'
_email = 'hello@jina.ai'
_keywords = (
    'jina neural-search neural-network deep-learning pretraining '
    'fine-tuning pretrained-models triplet-loss metric-learning '
    'siamese-network few-shot-learning'
)
_url = 'https://github.com/jina-ai/hubble-client-python/'
_download_url = 'https://github.com/jina-ai/hubble-client-python/tags'
_classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Environment :: Console',
    'Operating System :: OS Independent',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
]
_project_urls = {
    'Source': 'https://github.com/jina-ai/hubble-client-python/',
    'Tracker': 'https://github.com/jina-ai/hubble-client-python/issues',
}
_license = 'Proprietary'
_package_exclude = ['*.tests', '*.tests.*', 'tests.*', 'tests']


# package requirements
try:
    with open('requirements.txt', 'r') as f:
        _main_deps = f.readlines()
except FileNotFoundError:
    _main_deps = []


try:
    with open('requirements-dev.txt', 'r') as f:
        _extra_deps = {'full': f.read().splitlines()}
        _extra_deps['full'].remove('-r requirements.txt')
        _extra_deps['full'].extend(_main_deps)
except FileNotFoundError:
    _extra_deps = {}

# package long description
try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''


if __name__ == '__main__':
    setup(
        name='jina-hubble-sdk',
        packages=find_packages(exclude=_package_exclude),
        include_package_data=True,
        description=_description,
        author=_author,
        author_email=_email,
        url=_url,
        license=_license,
        download_url=_download_url,
        long_description=_long_description,
        long_description_content_type='text/markdown',
        zip_safe=False,
        setup_requires=_setup_requires,
        install_requires=_main_deps,
        extras_require=_extra_deps,
        python_requires=_python_requires,
        classifiers=_classifiers,
        project_urls=_project_urls,
        keywords=_keywords,
        entry_points={
            'console_scripts': [
                'jina-auth=hubble.__main__:main',
                'jina-hub=hubble.executor.__main__:main',
                'docker-credential-jina-hubble=hubble.dockerauth:main',
            ],
        },
    )
