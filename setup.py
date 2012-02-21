
from setuptools import setup, find_packages
import sys, os

version = '0.1.5'

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
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests']),
    
    #include_package_data=True,
    #zip_safe=True,
    #install_requires=[
    #    # -*- Extra requirements: -*-
    #],

    scripts = [
        'bin/fg-deploy-slurm.sh',
        'bin/fg-cluster-checkpoint.sh',
        'bin/fg-cluster-restore.sh',
        'bin/fg-cluster-shutdown.sh',
        'bin/fg-create-cluster.sh',
        'bin/fg-save-instances.sh',
        ],

    
    entry_points={
        'console_scripts': [
                'fg-cluster = futuregrid.virtual.cluster.fgc:main',
                'fg-local = futuregrid.virtual.cluster.info:localinfo', 
                'fg-info = futuregrid.virtual.cluster.info:info', 
             ]},

             #    install_requires = [
             #'setuptools',
             #'pip',
             #'fabric',
             #'boto',
             #],

    )
