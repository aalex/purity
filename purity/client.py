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
from purity import process

VERBOSE = False
VERYVERBOSE = False
_pure_data_managers = [] # global list of ProcessManager instances.

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
        self._pure_data_launcher = None # purity.server.PureData object.

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

    def start_purity_receiver(self):
        # TODO: rename to start_purity_receiver
        """ 
        You need to call this before launching the pd patch! 
        returns deferred
        """
        self._server_startup_deferred = defer.Deferred()
        self.fudi_server = fudi.FUDIServerFactory()
        self.fudi_server.register_message("__pong__", self.on_pong)
        self.fudi_server.register_message("__ping__", self.on_ping)
        self.fudi_server.register_message("__confirm__", self.on_confirm)
        self.fudi_server.register_message("__first_connected__", self.on_first_connected)
        self.fudi_server.register_message("__connected__", self.on_connected)
        if VERBOSE:
            print("reactor.listenTCP %d %s" % (self.receive_port, self.fudi_server))
        reactor.listenTCP(self.receive_port, self.fudi_server)
        #return self.fudi_server
        # TODO: add a timeout to this callback
        return self._server_startup_deferred

    def start_purity_sender(self):
        # TODO: rename to start_purity_sender
        """ 
        Starts purity sender. 
        returns deferred 
        """
        self.client_protocol = None
        if VERBOSE:
            print("Starting Purity/FUDI sender to port %d" % (self.send_port))
        deferred = fudi.create_FUDI_client('localhost', self.send_port, self.use_tcp)
        deferred.addCallback(self.on_client_connected)
        deferred.addErrback(self.on_client_error)
        return deferred

    def on_pong(self, protocol, *args):
        """ 
        Receives FUDI __pong__
        """
        if VERBOSE:
            print "received __pong__", args
        # print("stopping reactor")
        # reactor.stop()

    def on_ping(self, protocol, *args):
        """ 
        Receives FUDI __ping__
        """
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
        """ 
        Client can send messages to Pure Data 
        """
        self.client_protocol = protocol
        # self.client_protocol.send_message("ping", 1, 2.0, "bang")
        # print "sent ping"
        return protocol # pass it to the next

    def on_client_error(self, failure):
        """ 
        Client cannot send data to pd 
        """
        if VERBOSE:
            print "Error trying to connect.", failure
        raise Exception("Could not connect to pd.... Dying. %s" % (failure.getErrorMessage()))
        # print "stop"
        # reactor.stop()
    
    def __del__(self):
        """
        Destructor. Will try to stop the pd process.
        """
        self.stop()

    def quit(self):
        """
        Quits server and client.
        :return deferred:
        """
        #TODO: os.kill(self.pd_pid, sig)
        #FIXME : stopping pd process, buts still need to cleanup TCP listener
        if self._pure_data_launcher is not None:
            return self._pure_data_launcher._process_manager.stop()
        else:
            return defer.succeed(True)

    def quit_and_stop_reactor(self):
        """
        Wraps quit() and stops the reactor once Pure Data has quit.
        
        Typically, you would catch a KeyboardInterrupt and call this.
        """
        #FIXME: is this supposed to work at all? where are deferreds and callbacks?
        def _ok(result, d):
            reactor.stop()
            return result
        def _err(reason, d):
            reactor.stop()
            return reason
        d = self.quit()
        return d

    def send_message(self, selector, *args):
        """ 
        Send a message to pure data 
        """
        if self.client_protocol is not None:
            if VERYVERBOSE:
                print("Purity sends %s %s" % (selector, str(args)))
            self.client_protocol.send_message(selector, *args)
        else:
            print("Could not send %s" % (str(args)))
        #TODO: get rid of this
        if self.quit_after_message:
            print "stopping the application"
            reactor.callLater(0, reactor.stop)

    def create_patch(self, patch):
        """
        Sends the creation messages for a subpatch.
        """
        def _cl_drip_messages(self, messages, deferred):
            DELAY_BETWEEN_EACH = 0.01
            # wait 10 ms between each message.
            try:
                mess = messages.pop(0)
            except IndexError, e:
                deferred.callback(True) # done
            else:
                if VERBOSE:
                    print("%s" % (mess))
                self.send_message(*mess)
                reactor.callLater(DELAY_BETWEEN_EACH, _cl_drip_messages, 
                    self, messages, deferred) 
        mess_list = patch.get_fudi() # list of (fudi) lists
        deferred = defer.Deferred()
        _cl_drip_messages(self, mess_list, deferred)
        return deferred


def _create_managed_client(**server_kwargs):
    """
    Purity startup using the Process manager.
    
    1. Creates a Purity receiver... waits for __on_first_connected__ message.
    2. Launches Pure Data using the ProcessManager class.
    3. On loadbang, it receives the __on_first_connected__ message
    4. It then starts the Purity sender and callback its main deferred.

    Returns a Deferred.
    """
    # technique 2: using a process protocol. (much better)
    def _eb_sender_error(reason, my_deferred):
        if VERBOSE:
            print("Could not start purity sender: %s" % (reason.getErrorMessage()))
        my_deferred.errback(reason)
        #return reason #propagate error

    def _cb_sender_started(protocol, my_deferred, the_client):
        """
        Called when purity received __first_connected__
        """
        if VERBOSE:
            print("purity sender started")
        my_deferred.callback(the_client)
        #return the_client # pass client to next deferred.
    
    
    def _cb_both_started(result, my_deferred, purity_client):
        if VERBOSE:
            print("Both Pure Data patch and Purity listener are started.")
        sender_deferred = purity_client.start_purity_sender() 
        # start the fudi sender. should trigger its callback 
        # quite quickly is a [netreceives] is listening
        sender_deferred.addCallback(_cb_sender_started, my_deferred, purity_client)
        sender_deferred.addErrback(_eb_sender_error, my_deferred, purity_client)
    def _eb_both_error(reason, my_deferred, purity_client):
        my_deferred.errback(reason)
    
    def _cb_manager(result, purity_client):
        # this is just to register the PureData manager to purity client.
        global _pure_data_managers
        _pd = result
        _pure_data_managers.append(_pd._process_manager)
        purity_client.pure_data_launcher = _pd
        return result
    # ------------------------------
    my_deferred = defer.Deferred()
    purity_client = PurityClient(
        receive_port=15555, 
        send_port=17777, 
        quit_after_message=False) # create the client

    if VERBOSE: 
        print("created purity client: %s" % (purity_client))
        print("starting purity receiver")
    receiver_deferred = purity_client.start_purity_receiver() 
    #TODO: start_listener()
    #TODO : wait a bit here using a callLater ?
    manager_deferred = server.run_pd_manager(**server_kwargs) 
    manager_deferred.addCallback(_cb_manager, purity_client)
    # result will be PureData instance. (with a _process_manager attribute)
    # but we do not care for now.
    dl = [receiver_deferred, manager_deferred]
    d = process.deferred_list_wrapper(dl)
    d.addCallback(_cb_both_started, my_deferred, purity_client)
    d.addErrback(_eb_both_error, my_deferred, purity_client)
    # ... my_deferred will be triggered when all is done. 
    return my_deferred

def create_simple_client(**pd_kwargs):
    """
    New version of create_simple_client, but using 
    the managed process. Its deferred results in a purity client.
    :return: Deferred.
    """
    return _create_managed_client(**pd_kwargs)

def killall_pd():
    """
    Kills all running pure data children.
    """
    # TODO: make sure they are still running
    global _pure_data_managers
    dl = []
    for manager in _pure_data_managers:
        if VERBOSE:
            print("stopping pure data process manager %s" % (manager))
        d = manager.stop()
        dl.append(d)
    d = process.deferred_list_wrapper(dl)
    return d

def killall_pd_and_stop_reactor():
    """
    wraps killall_pd and stops reactor when done.
    You would typically call this once you catched a KeyboardInterrupt.
    """
    def _cb(result):
        reactor.stop()
        return result
    def _eb(reason):
        reactor.stop()
        return reason
    d = killall_pd()
    d.addCallback(_cb)
    d.addErrback(_eb)
