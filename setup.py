#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The Purity library for Pure Data dynamic patching.
#
# Copyright 2009 Alexandre Quessy
# <alexandre@quessy.net>
# http://alexandre.quessy.net
#
# Purity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Purity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the gnu general public license
# along with Purity.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Installation script for Purity.
---------------------------------

Usage::
  python setup.py build
  sudo python setup.py install --prefix=/usr/local

For developpers::
  sudo python setup.py develop --prefix=/usr/local
  sudo python setup.py develop --prefix=/usr/local --uninstall
"""
__version__ = "0.2.1"
DOWNLOAD_DIR = "http://alexandre.quessy.net/static/purity"
DOWNLOAD_FILE = "purity-%s.tar.gz" % (__version__)

from distutils.core import setup

#try:
#    from setuptools import find_packages
#    from setuptools import setup
#except ImportError, e:
#    print("You must install python-setuptools.")
#    print("Such as using \"sudo apt-get install python-setuptools\"")
#    import sys
#    sys.exit(1)

setup(
    name = "purity",
    version = __version__,
    author = "Alexandre Quessy",
    author_email = "alexandre@quessy.net",
    url = "http://wiki.dataflow.ws/Purity",
    description = "Purity dynamic patching library for Pure Data in Python.",
    long_description = """Purity is a Python library for Pure Data dynamic patching. The idea is to be able to harness the power of Pure Data for audio programming without having to use its graphical interface. Python's clear and intuitive syntax can be used with profit in order to create intricate patches with advanced string handling, graphical user interfaces and asynchronous network operations. Purity uses Twisted, an event-driven Python framework.
    """,
    #install_requires = ["twisted"], 
    #scripts = ["bin/purity-example.py"], 
    license = "GPL",
    platforms = ["any"],
    packages = ['purity', "purity/data", "purity/test"],# "purity/data"],
    package_data = {'purity':['data/*.pd']},
    ##"":["*.ttf", "*.rst", "*.png", "*.jpg", "*.pd"]
    download_url = "%s/%s" % (DOWNLOAD_DIR, DOWNLOAD_FILE),
    keywords = [], #TODO
    classifiers = [
        "Development Status :: 3 - Alpha", # api will change !
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.5",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )

#test_suite='nose.collector',
#      data_files = [
#         ('share/man/man1', [
#             'scripts/send_osc.1',
#             'scripts/dump_osc.1',
#         ]),
#     ],
 
