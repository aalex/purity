The Purity library for Pure Data dynamic patching.
--------------------------------------------------

Purity is a Python library for Pure Data dynamic patching. The idea is to be 
able to harness the power of Pure Data for audio programming without having 
to use its graphical interface. Python's clear and intuitive syntax can be 
used with profit in order to create intricate patches with advanced string 
handling, graphical user interfaces and asynchronous network operations. 
Purity uses Twisted, an event-driven Python framework.


LICENSE
-------

Copyright 2009 Alexandre Quessy
<alexandre@quessy.net>
http://alexandre.quessy.net

Purity is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Purity is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the gnu general public license
along with Purity.  If not, see <http://www.gnu.org/licenses/>.


INSTALLATION
------------

Install Pure Data and other tools::

  sudo apt-get install python-setuptools puredata mercurial python-twisted

Install Purity and start the example in a terminal window::

  mkdir -p ~/src
  cd ~/src/
  hg clone http://bitbucket.org/aalex/purity purity
  cd purity/
  sudo python setup.py build
  sudo python setup.py install --prefix=/usr/local
  ./examples/hello_metro.py

SEE ALSO
--------
You might want to learn to program in Python using Twisted. 
See http://twistedmatrix.com/

The officiel Purity Web site is a wiki located at 
http://wiki.dataflow.ws/Purity


