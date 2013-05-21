#!/usr/bin/python

import os
from setuptools import setup, find_packages

ROOT = os.path.abspath(os.path.dirname(__file__))
fp = open(os.path.join(ROOT, "requirements.txt"))
REQUIREMENTS = [r.strip() for r in fp.readlines()]
fp.close()


if __name__ == "__main__":
    setup(
        name="sshstdlib",
        version="1.4",
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

        data_files=[
            ("", ["requirements.txt", "README.md"])
        ],

        install_requires=REQUIREMENTS

    )
