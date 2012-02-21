from setuptools import setup

import sys, os

version = '0.1.2'

setup(
    name='futuregrid.virtual.cluster',
    version=version,
    description="The package allows the creation of a virtual cluster via SLURM and OpenStack",
    long_description="""\
The package allows the creation of a virtual cluster via SLURM and OpenStack
""",
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='FutureGrid OpenStack virtual cluster',
    author='Gregor von Laszewski, put othernames too',
    author_email='laszewski@gmail.com',
    url='http://futuregrid.org',
    license='Apache 2.0',
    package_dir = {'': '.'},
    packages = [
        'futuregrid.virtual.cluster'
        ],
    
    #include_package_data=True,
    #zip_safe=True,
    #install_requires=[
    #    # -*- Extra requirements: -*-
    #],
    
    entry_points={
        'console_scripts':
            ['fg-c = futuregrid.virtual.cluster.fgc:main', 
             ]},

             #    install_requires = [
             #        'setuptools',
             #        'pip',
             #        'fabric',
             #        'boto',
             #        ],

    )
