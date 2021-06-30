# SPDX-FileCopyrightText: 2021 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import setuptools

with open("README.md") as i:
    _long_description = i.read()

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

requirements_dev = []
with open('requirements-dev.txt') as f:
    requirements_dev = f.read().splitlines()

setuptools.setup(
    name="scancode-manifestor",
    version="0.0.1",
    author="Henrik Sanklef",
    author_email="hesa@sandklef.com",
    description="Scancode Manifestor",
    long_description=_long_description,
    long_description_content_type="text/markdown",
    license_files = ('LICENSE',),
    url="https://github.com/vinland-technology/scancode-manifestor",
    packages=['scancode_manifestor'],
    entry_points={
        "console_scripts": [
            "scancode-manifestor = scancode_manifestor.__main__:main",
        ]
    },
    package_data = {
        'scancode_manifestor': ['var/*'],
    },
    install_requires=requirements,
    extras_require={
        'dev': requirements_dev
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires='>=3.6',
)
