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
Simple example of a patch dynamically created using purity.
"""

from purity import client
from purity import canvas
from twisted.internet import reactor


def creation_callback(purity_client):
    """
    :param client: PurityClient instance.
    """
    main_patch = canvas.get_main_patch()
    # subpatch
    patch = main_patch.subpatch("metropatch", visible=True)
    # objects
    r = patch.receive("startme")
    tgl = patch.obj("tgl")
    metro = patch.obj("metro", 500)
    bang = patch.obj("bng")
    msg = patch.msg("world")
    printer = patch.obj("print", "hello")
    # connections
    patch.connect(r, 0, tgl, 0)
    patch.connect(tgl, 0, metro, 0)
    patch.connect(metro, 0, bang, 0)
    patch.connect(bang, 0, msg, 0)
    patch.connect(msg, 0, printer, 0)

    #print("purity_client: %s" % (purity_client))
    # send messages
    def _done(result, purity_client):
        purity_client.send_message("startme", 1)
    deferred = purity_client.create_patch(main_patch)
    #print "sent FUDI message:", "startme", 1
    deferred.addCallback(_done, purity_client)

if __name__ == "__main__":
    print("Starting purity !")
    deferred = client.create_simple_client()
    deferred.addCallback(creation_callback)
    try:
        reactor.run()
    except KeyboardInterrupt:
        print("Ctrl-C has been pressed.")
        reactor.stop()
    KILL_PD = True
    #KILL_PD = False
    if KILL_PD:
        import subprocess
        print("Killing all running pd processes.") # FIXME
        subprocess.call("killall pd", shell=True)

