#!/usr/bin/env python
#
# ToonLoop for Python
#
# Copyright 2008 Alexandre Quessy & Tristan Matthews
# <alexandre@quessy.net> & <le.businessman@gmail.com>
# http://www.toonloop.com
#
# Original idea by Alexandre Quessy
# http://alexandre.quessy.net
#
# ToonLoop is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ToonLoop is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the gnu general public license
# along with ToonLoop.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Pure Data sampler using Python and Purity.

Patch dynamically created using purity.
"""
from twisted.internet import gtk2reactor
gtk2reactor.install() # has to be done before importing reactor
import gtk
from twisted.internet import reactor
import sys
import os
from purity import client
from purity import canvas

TABLE_PREFIX = "table_"
ADC_INDEX = 1 # which audio input to record from
NUM_TABLES = 16
NUM_PLAYERS = 8
SAMPLING_RATE = 48000
ARRAY_DURATION = 2.0
OUTPUT_CATCH = "output"

class Player(object):
    """
    A player plays a sound.

    [r play]
    "set $1", "bang"
    [tabread~]
    [line~]
    [dbtorms~]
    [*~]
    [throw~ out]
    """
    #TODO: voice stealing or not
    #TODO: adsr
    def __init__(self, id, main_patch, sampler):
        self.sampler = sampler
        table_name = TABLE_PREFIX + str(0)
        self.id = id
        self.patch = main_patch.subpatch("player_" + str(self.id))
        self.r_play = self.patch.receive("play_" + str(self.id))
        self.tabplay = self.patch.obj("tabplay~", table_name)
        self.throw = self.patch.obj("throw~", OUTPUT_CATCH)
        # connections
        self.patch.connect(self.r_play, 0, self.tabplay, 0)
        self.patch.connect(self.tabplay, 0, self.throw, 0)

    def play(self, index):
        """
        Sends to [tabread~] the message to play the table index given as argument.
        :param index: int Table number.
        """
        self.r_play.set_client(self.sampler.client)
        self.r_play.send("stop")
        self.r_play.send("set", "%s%d" % (TABLE_PREFIX, index))
        self.r_play.send("bang")

class Recorder(object):
    """
    Recording subpatch.

    [adc~ 3]     [receive record]    ("set $1", "bang")
    [*~ 1]
    [tabwrite~]
    """
    def __init__(self, main_patch, sampler):
        self.sampler = sampler
        table_name = TABLE_PREFIX + str(0)
        self.patch = main_patch.subpatch("recording")
        self.adc = self.patch.obj("adc~", ADC_INDEX)
        self.r_rec = self.patch.receive("rec")
        self.tabwrite = self.patch.obj("tabwrite~", table_name)
        self.patch.connect(self.adc, 0, self.tabwrite, 0)
        self.patch.connect(self.r_rec, 0, self.tabwrite, 0)

    def record(self, table_index=0, start=True):
        self.r_rec.set_client(self.sampler.client)
        if start:
            self.r_rec.send("stop") # first stop
            self.r_rec.send("set", "%s%d" % (TABLE_PREFIX, table_index)) # self.current_rec_table)
            self.r_rec.send("bang")
        else:
            self.r_rec.send("stop")

class Output(object):
    """
    Audio output subpatch.

    [catch~] --> [*~] --> [dac~]
    """
    def __init__(self, main_patch):
        self.patch = main_patch.subpatch("output")
        self.catch = self.patch.obj("catch~", OUTPUT_CATCH)
        self.mult = self.patch.obj("*~", 1.0) # #1.0 / NUM_PLAYERS)
        self.dac = self.patch.obj("dac~", 1, 2)
        self.patch.connect(self.catch, 0, self.mult, 0)
        self.patch.connect(self.mult, 0, self.dac, 0)
        self.patch.connect(self.mult, 0, self.dac, 1)

class Sampler(object):
    """
    Pure Sampler main Pure Data patch.

    [table array-$N <samples>]
    """
    def __init__(self):
        self.client = None
        self.main_patch = canvas.get_main_patch()
        # ---------------- buffers
        self.tables_subpatch = self.main_patch.subpatch("buffers")
        for i in range(NUM_TABLES):
            self.tables_subpatch.obj("table", "table_" + str(i), int(SAMPLING_RATE * ARRAY_DURATION))
        # -------------- players
        self.players = {} # key is an index.
        for i in range(NUM_PLAYERS):
            self.players[i] = Player(i, self.main_patch, self)
        # ------------------- recorder
        self.recorder = Recorder(self.main_patch, self)
        # ------------------- output
        self.output = Output(self.main_patch)
        self.current_player = 0
    
    def record(self, table_index=0, start=True):
        print("send record?")
        self.recorder.record(table_index, start)

    def play(self, table_index):
        print("send play?")
        self.current_player = (self.current_player + 1) % NUM_PLAYERS
        self.players[self.current_player].play(table_index) # TODO: voice stealing?

    def creation_callback(self, client):
        """
        :param client: PurityClient instance.
        """
        self.client = client
        # send creation messages
        client.create_patch(self.main_patch)
        client.send_message("__enable_verbose__", 1)
        client.send_message("pd", "dsp", 1)
        #print "sent FUDI message:", "startme", 1
        #client.send_message("startme", 1)


class SimpleSamplerApp(object):
    """
    Simple GTK2 GUI for the puresamler.
    
    Defines the main window
    """
    def __init__(self, sampler=None):
        self.sampler = sampler
        # Window and framework
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", self.destroy)

        # Box for multiple widgits
        self.box1 = gtk.VBox(False, 0)
        self.window.add(self.box1)

        # Buttons
        self.hboxes = {}
        self.labels = {}
        self.rec_buttons = {}
        self.play_buttons = {}

        for i in range(NUM_TABLES):
            self.hboxes[i] = gtk.HBox(False, 0)
            self.box1.pack_start(self.hboxes[i], True, True, 0)

            self.labels[i] = gtk.Label("#%d" % (i))
            self.hboxes[i].pack_start(self.labels[i], True, True, 0)
            self.labels[i].show()

            self.rec_buttons[i] = gtk.Button("Record")
            self.rec_buttons[i].connect("clicked", self.on_rec, i)
            self.hboxes[i].pack_start(self.rec_buttons[i], True, True, 0)
            self.rec_buttons[i].show()

            self.play_buttons[i] = gtk.Button("Play")
            self.play_buttons[i].connect("clicked", self.on_play, i)
            self.hboxes[i].pack_start(self.play_buttons[i], True, True, 0)
            self.play_buttons[i].show()
            
            self.hboxes[i].show()

        self.lastbutton = gtk.Button("Quit")
        self.lastbutton.connect("clicked", self.destroy)
        self.box1.pack_start(self.lastbutton, True, True, 0)
        self.lastbutton.show()

        # Show the box
        self.box1.show()

        # Show the window
        self.window.show()


    def on_rec(self, widget, info): # index as info
        """
        Callback function for use when the button is pressed
        """
        #print "Button %s was pressed" % (info)
        print "Rec %d" % (info)
        if self.sampler is not None:
            self.sampler.record(int(info))

    def on_play(self, widget, info): # index as info
        #print "Button %s was pressed" % (info)
        print "Play %d" % (info)
        if self.sampler is not None:
            self.sampler.play(int(info))


    def destroy(self, widget, data=None):
        """
        Destroy method causes appliaction to exit
        when main window closed
        """
        def _done(message):
            print("_done !")
            print(message)
            gtk.main_quit()
            print("reactor.stop()")
            reactor.stop()
            #print("sys.exit(0)")
            #sys.exit(0) # TODO: kill child
            
        print("Quit")
        if self.sampler.client is not None:
            deferred = self.sampler.client.quit()
            deferred.addCallback(_done)
        else:
            _done("No Purity client to quit.")


    def main(self):
        """
        All PyGTK applications need a main method - event loop
        """
        gtk.main()

if __name__ == "__main__":
    print("This pid is %d" % (os.getpid()))
    sampler = Sampler()
    deferred = client.create_simple_client()
    deferred.addCallback(sampler.creation_callback)
    app = SimpleSamplerApp(sampler)
    try:
        reactor.run()
    except KeyboardError:
        print("Ctrl-C has been pressed.")
    import subprocess
    print("Killing all running pd processes.") # FIXME
    subprocess.call("killall pd", shell=True)

