#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Miville
# Copyright (C) 2008 Société des arts technologiques (SAT)
# http://www.sat.qc.ca
# All rights reserved.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Miville is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Miville.  If not, see <http://www.gnu.org/licenses/>.
"""
Tools for deferreds, delayed calls and process management.
"""
import os

from twisted.internet import defer
from twisted.internet import error
from twisted.python import failure
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import procutils

#from miville.utils import observer
#from miville.utils import log
#
#log = log.start("info", 1, 0, "streams.tools")
class Logger(object):
    levels = {1:"critical", 2:"error", 3:"warning", 4:"info", 5:"debug"}
    def __init__(self, level=4):
        self.level = level
    def critical(self, txt):
        self._log(txt, 1)
    def error(self, txt):
        self._log(txt, 2)
    def warning(self, txt):
        self._log(txt, 3)
    def info(self, txt):
        self._log(txt, 4)
    def debug(self, txt):
        self._log(txt, 5)
    def _log(self, txt, level):
        if level <= self.level:
            print(txt) # for now
# global var
log = Logger(4)

class AsynchronousError(Exception):
    """
    Raised by DeferredWrapper or DelayedWrapper
    """
    pass
class ManagedProcessError(Exception):
    """
    Raised by ProcessManager
    """
    pass

class DeferredWrapper(object):
    """
    Wraps a Deferred.
    We need to know if it has been called or not.
    """
    def __init__(self):
        self.deferred = None
        self.is_called = False
        self.is_success = None
        self._created = False
    
    def make_deferred(self):
        """
        Returns a Deferred
        """
        if self._created:
            raise AsynchronousError("This Deferred has already been set up.")
        else:
            self.deferred = defer.Deferred()
            self._created = True
            return self.deferred
    
    def callback(self, result):
        """
        Wraps Deferred.callback(result)
        """
        if not self._created:
            raise AsynchronousError("This Deferred has not been set up yet.")
        else:
            if not self.is_called:
                self.is_success = True
                self.is_called = True
                log.debug("Calling deferred callback %s" % (result))
                self.deferred.callback(result)
            else:
                pass # TODO: add a warning
    
    def errback(self, error):
        """
        Wraps Deferred.errback(error)
        """
        if not self._created:
            raise AsynchronousError("This Deferred has not been set up yet.")
        else:
            if not self.is_called:
                self.is_success = False
                self.is_called = True
                log.debug("Calling deferred errback %s" % (error))
                self.deferred.errback(error)
            else:
                pass # TODO: add a warning

class DelayedWrapper(object):
    """
    Wraps reactor.callLater and twisted.internet.base.DelayedCall
    Adds a Deferred to it.

    You must call the call_later method once an instance is created.
    """
    def __init__(self): #, delay, callback, *args, **kwargs):
        """
        Wraps reactor.callLater(...)
        """
        self.deferred_wrapper = None
        self._to_call = None
        self.delayed_call = None
        self._args = []
        self._kwargs = {}
        self.is_called = False
        self.is_cancelled = False
        self.is_scheduled = False
    
    def call_later(self, delay, function, *args, **kwargs):
        """
        Returns a Deferred
        
        :param delay: Duration in seconds.
        :param function: callable
        :param args: list or args to pass to function to call.
        """
        self._to_call = function
        self.deferred_wrapper = DeferredWrapper()
        self._args = args
        self._kwargs = kwargs
        self.delayed_call = reactor.callLater(delay, self._call_it)
        self._args = args
        self._kwargs = kwargs
        self.is_scheduled = True
        log.debug("Creating delayed (%f s) %s" % (delay, function))
        return self.deferred_wrapper.make_deferred()
    
    def _call_it(self):
        log.debug("Calling delayed %s" % (self._to_call))
        if self.is_scheduled:
            result = self._to_call(*self._args, **self._kwargs)
            if isinstance(result, failure.Failure):
                self.deferred_wrapper.errback(result)
            else:
                self.deferred_wrapper.callback(result)
            self.is_called = True

    def cancel(self, result):
        """
        Cancels the delayed call.
        
        If result is a Failure, calls the deferred errback, otherwise, calls it callback
        with the result.
        """
        # TODO: verify this, test it, and think about it.
        if self.is_scheduled and not self.is_cancelled and not self.is_called:
            try:
                self.delayed_call.cancel()
            except error.AlreadyCancelled, e:
                pass #self.is_cancelled = True
            except error.AlreadyCalled, e:
                pass #self.is_called = True
            else:
                log.debug("Cancelling delayed %s giving it result %s" % (self._to_call, result))
                self.is_cancelled = True
                if isinstance(result, failure.Failure):
                    self.deferred_wrapper.errback(result)
                else:
                    self.deferred_wrapper.callback(result)
                self.is_cancelled = True
            #return defer.fail(failure.Failure(StreamError("Cannot stop process. Process is not running.")))

def deferred_list_wrapper(deferreds):
    """
    Wraps a DeferredList. All results are strings and are concatenated !!
    
    You should add individual callbacks to each deferred prior to pass it as an argument to this function. In this case, do not forget to return the result in the callbacks.
    
    :param deferreds: list of Deferred instances.
    """
    def _cb(result, d):
        overall_success = True
        overall_msg = ""
        overall_err_msg = ""
        #exc_type = AsynchronousError # type of exception
        #_failure = None
        for (success, value) in result:
            if success:
                overall_msg += str(value)
                #log.debug("defereredlist wrapper : success: %s" % (value))
            else:
                overall_success = False
                msg = value.getErrorMessage()
                #_failure = success # takes the last failure and throw it !
                overall_err_msg += msg
                #log.debug("deferrelist wrapper : failure: %s" % (msg))
        if overall_success:
            log.debug("deferredlist wrapper : overall success")
            d.callback(overall_msg)
        else:
            log.debug("deferredlist wrapper : overall error")
            # TODO:
            # we use to concatenate the error messages and fail with 
            # an AsynchronousError :
            # d.errback(failure.Failure(AsynchronousError(overall_err_msg)))
            # Now, we errback with the last failure in the deferred list 
            # in order to keep the original exception type
            # d.errback(_failure)
            d.errback(failure.Failure(AsynchronousError(overall_err_msg)))
    d = defer.Deferred()
    dl = defer.DeferredList(deferreds, consumeErrors=True)
    dl.addCallback(_cb, d) # this deferred list needs no errback
    return d

class TextLinesLogger(object):
    """
    Logs lines of text.
    """
    def __init__(self, maxsize=0, prefix=""):
        self.lines = []
        self.maxsize = maxsize
        self.prefix = prefix

    def append(self, line):
        self.lines.append(line.strip())
        if self.maxsize != 0:
            if len(self.lines) > self.maxsize:
                self.lines.pop(0)
    
    def get_text(self):
        """
        Returns the whole text logged.
        """
        ret = ""
        for line in self.lines:
            ret += self.prefix + line + "\n"
        return ret
    
    def clear(self):
        """
        Empties the lines of text
        """
        self.lines = []

# ---------------------------- process stuff ----------------


class ManagedProcessProtocol(protocol.ProcessProtocol):
    """
    Process managed by a ProcessManager.
 
    Its stdin/stdout streams are logged.    
    """
    def __init__(self, manager):
        """
        :param manager: ProcessManager instance.
        """
        self.manager = manager
    
    def connectionMade(self):
        """
        Called once the process is started.
        """
        self.manager._on_connection_made()

    def outReceived(self, data):
        """
        Called when text is received from the managed process stdout
        """
        self.manager._on_out_received(data)

    def errReceived(self, data):
        """
        Called when text is received from the managed process stderr
        """
        self.manager._on_err_received(data) 

    def processEnded(self, status):
        """
        Called when the managed process has exited.
        status is probably a twisted.internet.error.ProcessTerminated
        "A process has ended with a probable error condition: process ended by signal 1"
        """
        # This is called when all the file descriptors associated with the child 
        # process have been closed and the process has been reaped. This means it 
        # is the last callback which will be made onto a ProcessProtocol. 
        # The status parameter has the same meaning as it does for processExited.
        self.manager._on_process_ended(status)
    
    def inConnectionLost(self, data):
        log.debug("stdin pipe has closed." + str(data))
    def outConnectionLost(self, data):
        log.debug("stdout pipe has closed." + str(data))
    def errConnectionLost(self, data):
        log.debug("stderr pipe has closed." + str(data))
    def processExited(self, reason):
        """
        This is called when the child process has been reaped, and receives 
        information about the process' exit status. The status is passed in the form 
        of a Failure instance, created with a .value that either holds a ProcessDone 
        object if the process terminated normally (it died of natural causes instead 
        of receiving a signal, and if the exit code was 0), or a ProcessTerminated 
        object (with an .exitCode attribute) if something went wrong.
        """
        log.debug("process has exited " + str(reason))

class ProcessManager(object):
    """
    Starts one  ManagedProcessProtocol.
    
    You should create one ProcessManager each time you start a process, and delete it after.
    """
    # constants
    STATE_IDLE = "IDLE" 
    STATE_STARTING = "STARTING"
    STATE_RUNNING = "RUNNING" # success
    STATE_STOPPING = "STOPPING"
    STATE_STOPPED = "STOPPED" # success
    STATE_ERROR = "ERROR"
    # default that can be overriden in children classes.
    
    def __init__(self, name="default", log_max_size=100, command=None, verbose=False, process_protocol_class=ManagedProcessProtocol, check_delay=2.0):
        """
        :param command: list or args. The first item is the name of the executable.
        :param name: Name of the process, for printing infos, etc.
        Might raise a ManagedProcessError
        """
        self.name = name
        self.command = list(command)
        if command is None:
            raise ManagedProcessError("You must provide a command to be run.")
        else:
            try:
                self.command[0] = procutils.which(self.command[0])[0]
            except IndexError:
                raise ManagedProcessError("Could not find path of executable %s." % (self.command[0]))
                
        self.process_protocol_class = process_protocol_class
        self.state = self.STATE_IDLE
        self.stdout_logger = TextLinesLogger(maxsize=log_max_size, prefix=self.name)
        self.stderr_logger = TextLinesLogger(maxsize=log_max_size, prefix=self.name)
        self.verbose = verbose
        self.check_delay = check_delay
        self._process_protocol = None
        self._process_transport = None
        self._startup_check = None # DelayedWrapper 
        self._shutdown_check = None # DelayedWrapper 

    def start(self):
        """
        Start the managed process
        
        Returns a Deferred.
        """
        self.stdout_logger.clear()
        self.stderr_logger.clear()
        self._process_protocol = ManagedProcessProtocol(self)
        if self.verbose:
            print("Running command %s" % (str(" ".join(self.command))))
        try:
            proc_path = self.command[0]
            args = self.command
            environ = {}
            for key in ['HOME', 'DISPLAY', 'PATH']: # passing a few env vars
                if os.environ.has_key(key):
                    environ[key] = os.environ[key]
            self.state = self.STATE_STARTING
            log.debug("Starting process (%s) %s %s" % (self.name, self.command, environ))
            self._process_transport = reactor.spawnProcess(self._process_protocol, proc_path, args, environ, usePTY=True)
        except TypeError, e:
            # print(str(e))
            self.state = self.STATE_ERROR
            #self.subject.notify(None, str(e), "start_error")
            return defer.fail(failure.Failure(ManagedProcessError(str(e))))
        else:
            self._startup_check = DelayedWrapper()
            deferred = self._startup_check.call_later(self.check_delay, self._cl_check_if_started)
            return deferred

    def _on_connection_made(self):
        if self.STATE_STARTING:
            self.state = self.STATE_RUNNING
            #return result # important to return something from deferred callbacks
        else:
            self.state = self.STATE_ERROR
            #return fail.Failure(ManagedProcessError("Startup success has been calle more than once !"))
        
    def _cl_check_if_started(self):
        """
        Called later after start() has been called.
        The value it returns is given to the callback of this start() method.
        """
        # called later.
        if self.state is self.STATE_RUNNING:
            #self.subject.notify(None, True, "start_success") 
            #print self.subject.observers.values()
            return True #self._startup_check.callback(True) # success !
        else:
            output = "%s\n%s" % (self.stdout_logger.get_text(), self.stderr_logger.get_text())
            #self._startup_check.errback(
            err_msg = "Could not start process %s. " % (self.name)
            if self.state is self.STATE_ERROR:
                err_msg += "It crashed. "
            else:
                err_msg += "It state is %s. " % (self.state)
            err_msg += "\nHere is its output:\n %s" % (self.format_output_when_crashed(output))
            #self.subject.notify(None, err_msg, "start_error")
            return failure.Failure(ManagedProcessError(err_msg)) # Important to return the failure

    def format_output_when_crashed(self, output):
        # default does nothing
        return output

    def _on_out_received(self, data):
        log.debug("Logging(%s): %s" % (self.name, data))
        self.stdout_logger.append(data.strip())

    def _on_err_received(self, data):
        self.stderr_logger.append(data.strip())

    def stop(self):
        """
        Stops the managed process
        Returns a Deferred.
        """
        if self.state == self.STATE_RUNNING:
            self.state = self.STATE_STOPPING
            self._shutdown_check = DelayedWrapper()
            deferred = self._shutdown_check.call_later(self.check_delay, self._cl_check_if_stopped)
            self._process_transport.loseConnection()
            return deferred
        else:
            #old_state = self.state
            #self.state = self.STATE_ERROR
            #err_msg = "Cannot stop %s process because it is in %s state." % (self.name, old_state)
            #self.subject.notify(None, err_msg, "stop_error")
            #return defer.fail(failure.Failure(ManagedProcessError(err_msg)))
            msg = "Stopped process even if it was in an %s state." % (self.state)
            self.state = self.STATE_STOPPED
            return defer.succeed(msg)

    def _on_process_ended(self, reason):
        if self.state == self.STATE_STARTING:
            self.state = self.STATE_ERROR
            #self._startup_check.cancel() # triggers the callback
        elif self.state == self.STATE_RUNNING:
            self.state = self.STATE_ERROR
            # TODO: notify some observer that it crashed
            #self.subject.notify(None, True, "crashed") # what other value could we add here?
        elif self.state == self.STATE_STOPPING:
            self.state = self.STATE_STOPPED
            #self._shutdown_check.cancel() # triggers the callback
        if self.verbose:
            print("%s process ended. Reason: \n%s" % (self.name, str(reason)))

    def _cl_check_if_stopped(self):
        """
        Called later after stop() has been called.
        The value it returns is given to the callback of this stop() method.
        """
        # called later.
        if self.state == self.STATE_STOPPED:
            #self.subject.notify(None, True, "stop_success")
            return True #self._shutdown_check.callback(True) # success !
        else:
            output = "%s\n%s\n" % (self.stdout_logger.get_text().strip(), self.stderr_logger.get_text().strip())
            #self._startup_check.errback(
            err_msg = "Process %s : error while trying to stop it. It is in state %s. Output :\n%s" % (self.name, self.state, output)
            #self.subject.notify(None, err_msg, "stop_error")
            return failure.Failure(ManagedProcessError(err_msg))


