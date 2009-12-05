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
import random
from purity import client
from purity import canvas
from twisted.internet import reactor
from twisted.internet import task

RUNNING = True
VERBOSE = False

def audio_patch(purity_client):
    """
    Random notes example.

    [r note] --> [mtof] --> [pack f 50] --> [line~] --> 
    [osc~] --> [*~ 0.25] ==> [dac~]
    """
    main = canvas.get_main_patch()
    patch = main.subpatch("sinepatch", visible=True)
    # objects
    r = patch.receive("note")
    mtof = patch.obj("mtof")
    pack = patch.obj("pack", "f", 50) # 150 ms
    line = patch.obj("line~")
    osc = patch.obj("osc~", 440)
    mult = patch.obj("*~", 0.125)
    dac = patch.obj("dac~", 1, 2)
    # connections
    patch.connect(r, 0, mtof, 0)
    patch.connect(mtof, 0, pack, 0)
    patch.connect(pack, 0, line, 0)
    patch.connect(line, 0, osc, 0)
    patch.connect(osc, 0, mult, 0)
    patch.connect(mult, 0, dac, 0)
    patch.connect(mult, 0, dac, 1) # stereo
    
    def _done(result, purity_client):
        def send_random_note(purity_client):
            global RUNNING
            note = random.randint(48, 72)
            delay = 0.15
            if VERBOSE:
                print("note %f" % (note))
            purity_client.send_message("note", note, delay) # ms
        purity_client.send_message("pd", "dsp", 1)
        looping_call = task.LoopingCall(send_random_note, (purity_client))
        looping_call.start(0.15)
        #reactor.callLater(0.1, send_random_note, purity_client, send_random_note)
    # send messages
    deferred = purity_client.create_patch(main)
    deferred.addCallback(_done, purity_client)

if __name__ == "__main__":
    deferred = client.create_simple_client(
        rate=48000, 
        #driver="jack", 
        driver="alsa", 
        nogui=True
        )
    deferred.addCallback(audio_patch)
    try:
        reactor.run()
    except KeyboardInterrupt:
        print("Quitting.")
    import subprocess
    print("Killing all running pd processes.") # FIXME
    subprocess.call("killall pd", shell=True)

