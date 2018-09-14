from setuptools import setup, find_packages
#from pip._internal.req import parse_requirements
from pip.req import parse_requirements

setup(
    name='openedx2zim',
    version='0.5.1',
    description="Make zimfile from open edx MOOCs",
    long_description=open('README.md').read(),
    author='dattaz',
    author_email='taz@dattaz.fr',
    url='http://github.com/kiwix/openedx',
    keywords="kiwix zim openedx edx offline",
    license="GPL",
    #packages=find_packages('.'),
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'openedxtozim': 'openedxtozim'},
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'docopt',
        'bs4',
        'lxml',
        'webvtt-py',
        'youtube-dl',
        'python-slugify',
        'jinja2',
        'mistune',
        'requests',
        'iso-639'
        ],
    platforms='Linux',
    scripts=['openedx2zim'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4'
    ],
)
