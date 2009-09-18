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
try:
    from setuptools import find_packages
    from setuptools import setup
except ImportError, e:
    print("You must install python-setuptools.")
    print("Such as using \"sudo apt-get install python-setuptools\"")

setup(
    name = "purity",
    version = "0.1",
    author = "Alexandre Quessy",
    author_email = "alexandre@quessy.net",
    url = "http://alexandre.quessy.net/",
    description = "Purity dynamic patching library for Pure Data.",
    long_description = """Python asynchronous tools for writing audio graphs dynamically.""",
    install_requires = ["twisted"], 
    scripts = ["scripts/purity-example.py"], 
    license = "GPL",
    platforms = ["any"],
    zip_safe = False,
    packages = ['purity'],
    package_data = {
        "":["*.ttf", "*.rst", "*.png", "*.jpg", "*.pd"]
    }
    )

#test_suite='nose.collector',
#      data_files = [
#         ('share/man/man1', [
#             'scripts/send_osc.1',
#             'scripts/dump_osc.1',
#         ]),
#     ],
 
