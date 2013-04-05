#!/usr/bin/python

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="sshstdlib",
        version="1.0",
        license="BSD",

        description="A standard library emulation layer over SSH",
        author="Steve Stagg",
        author_email="stestagg@gmail.com",
        url="http://github.com/stestagg/sshstdlib",

        packages=find_packages("src"),
        package_dir={"": "src"},

        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],

        install_requires=[
            "fin",
            "paramiko"
        ]

    )
