from setuptools import setup, find_packages
from pip.req import parse_requirements

setup(
    name='openedx2zim',
        version='0.1',
    description="Make zimfile from open edx MOOCs",
    long_description=open('README.md').read(),
    author='dattaz',
    author_email='taz@dattaz.fr',
    url='http://github.com/kiwix/openedx',
    keywords="kiwix zim openedx edx offline",
    license="GPL",
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'docopt',
        'bs4',
        'lxml',
        'webvtt-py',
        'youtube-dl',
        'awesome-slugify',
        'jinja2',
        'mistune'
        ],
    zip_safe=False,
    platforms='Linux',
    include_package_data=True,
    entry_points={
            'console_scripts': ['openedx2zim=openedx.openedx2zim:run'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4'
    ],
)
