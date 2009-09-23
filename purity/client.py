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
Simpler FUDI sender.
"""
import sys
import os
from twisted.internet import reactor
from twisted.internet import defer
from purity import fudi
from purity import server

VERBOSE = True

class PurityClient(object):
    """
    Dynamic patching Pure Data message sender.
    Used for dynamic patching with Pd.
    """
    # TODO: connect directly to pd-gui port, which is 5400 + n
    def __init__(self, receive_port=14444, send_port = 15555, use_tcp=True, quit_after_message=False, pd_pid=None):
        self.send_port = send_port
        self.receive_port = receive_port
        self.client_protocol = None
        self.fudi_server = None
        self.use_tcp = use_tcp # TODO
        self.quit_after_message = quit_after_message
        self._server_startup_deferred = None
        self.pd_pid = pd_pid # maybe None

    def register_message(self, selector, callback):
        """
        Registers a listener for a message selector.
        The selector is how we call the first atom of a message.
        An atom is a word. Atoms are separated by the space character.

        :param selector: str
        :param callback: callable
        @see purity.fudi.FUDIServerFactory.register_message
        """
        if self.fudi_server is not None: # TODO: more checking
            self.fudi_server.register_message(selector, callback)

    def server_start(self):
        """ returns server """
        self._server_startup_deferred = defer.Deferred()
        self.fudi_server = fudi.FUDIServerFactory()
        self.fudi_server.register_message("__pong__", self.on_pong)
        self.fudi_server.register_message("__ping__", self.on_ping)
        self.fudi_server.register_message("__confirm__", self.on_confirm)
        self.fudi_server.register_message("__first_connected__", self.on_first_connected)
        self.fudi_server.register_message("__connected__", self.on_connected)
        reactor.listenTCP(self.receive_port, self.fudi_server)
        #return self.fudi_server
        # TODO: add a timeout to this callback
        return self._server_startup_deferred

    def client_start(self):
        """ 
        Starts sender. 
        returns deferred """
        self.client_protocol = None
        if VERBOSE:
            print("Starting FUDI client sending to %d" % (self.send_port))
        deferred = fudi.create_FUDI_client('localhost', self.send_port, self.use_tcp)
        deferred.addCallback(self.on_client_connected)
        deferred.addErrback(self.on_client_error)
        return deferred

    def on_pong(self, protocol, *args):
        """ Receives FUDI __pong__"""
        print "received __pong__", args
        # print("stopping reactor")
        # reactor.stop()

    def on_ping(self, protocol, *args):
        """ Receives FUDI __ping__"""
        if VERBOSE:
            print "received __ping__", args

    def on_confirm(self, protocol, *args):
        """ 
        Receives FUDI __confirm__ for the confirmation of every FUDI message sent
        to Pure Data. You need to send Pure Data a "__enable_confirm__ 1" message.
        """
        if VERBOSE:
            print "received __confirm__", args

    def on_first_connected(self, protocol, *args):
        """ 
        Receives FUDI __first_connected__ when the Pure Data application 
        is ready and can send FUDI message to Python.
        """
        if VERBOSE:
            print "received __first_connected__", args
        self._server_startup_deferred.callback(self.fudi_server)
    
    def on_connected(self, protocol, *args):
        """ 
        Receives FUDI __connected__ when the Pure Data application 
        connects or re-connects after a disconnection.
        """
        if VERBOSE:
            print "received __connected__", args

    def on_client_connected(self, protocol):
        """ Client can send messages to Pure Data """
        self.client_protocol = protocol
        # self.client_protocol.send_message("ping", 1, 2.0, "bang")
        # print "sent ping"
        return protocol # pass it to the next

    def on_client_error(self, failure):
        """ Client cannot send data to pd """
        print "Error trying to connect.", failure
        raise Exception("Could not connect to pd.... Dying.")
        # print "stop"
        # reactor.stop()
    
    def quit(self):
        """
        Quits server and client.
        :return deferred:
        """
        deferred = defer.Deferred()
        def _kill_server(deferred):
            try:
                sig = 9
                os.kill(self.pd_pid, sig)
                mess = "Killed Pure Data successfully."
            except OSError, e:
                mess = "Pure Data quit successfully."
            deferred.callback(mess)
        self.send_message("pd", "quit")

        if self.pd_pid is not None:
            reactor.callLater(0.5, _kill_server, deferred)
        return deferred

    def send_message(self, selector, *args):
        """ Send a message to pure data """
        if self.client_protocol is not None:
            if VERBOSE:
                print("Purity sends %s %s" % (selector, str(args)))
            # if fudi.VERBOSE:
            # print("sending %s" % (str(args)))
            # print args[0], args[1:]
            # args = list(args[1:])
            # atom = args[0]
            # print("will send %s %s" % (selector, args))
            # self.client_protocol.send_message(*args, selector)
            self.client_protocol.send_message(selector, *args)
        else:
            print("Could not send %s" % (str(args)))
        if self.quit_after_message:
            print "stopping the application"
            # TODO: try/catch
            reactor.callLater(0, reactor.stop)

    def create_patch(self, patch):
        """
        Sends the creation messages for a subpatch.
        """
        mess_list = patch.get_fudi() # list of (fudi) lists
        # print(mess_list)
        for mess in mess_list:
            self.send_message(*mess)

def create_simple_client(**server_kwargs):
    """
    Creates a purity server (Pure Data process manager)
    and a purity client. 
    """
    # TODO: receive message from pd to know when it is really ready.
    def _callback(protocol, my_deferred, the_client):
        my_deferred.callback(the_client)
        return True
    
    def _connected(the_server, my_deferred, the_client):
        # time.sleep(1.0) # Wait until pd is ready. #TODO: use netsend instead.
        c_deferred = the_client.client_start() # start it
        c_deferred.addCallback(_callback, my_deferred, the_client)
    
    my_deferred = defer.Deferred()
    pid = server.fork_and_start_pd(**server_kwargs)
    if pid != 0:
        the_client = PurityClient(
            receive_port=15555, 
            send_port=17777, 
            quit_after_message=False, 
            pd_pid=pid,
            use_tcp=True) # create the client
        s_deferred = the_client.server_start()
        # TODO: use deferred with __connected__ instead of callLater.
        #reactor.callLater(5.0, _later, my_deferred, the_client)
        s_deferred.addCallback(_connected, my_deferred, the_client)
    else:
        sys.exit(0) # do not do anything else here !
    return my_deferred


def create_patch(fudi_client, patch):
    """
    Sends the creation messages for a subpatch.
    DEPRECATED. Use client.create_patch(patch) instead.
    """
    mess_list = patch.get_fudi() # list of (fudi) lists
    # print(mess_list)
    for mess in mess_list:
        if VERBOSE:
            print("%s" % (mess))
        fudi_client.send_message(*mess)

