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
Launcher for a Pure Data process.
"""
import os
import sys
import subprocess
import purity
from purity import process
from twisted.internet import defer

VERBOSE = True
DYNAMIC_PATCH = os.path.join(os.path.dirname(purity.__file__), "data", "dynamic_patch.pd")

#class ChildKilledError(Exception):
#    """Raised when child is killed"""
#    pass

#def run_command(command_str, variables_dict={}, die_on_ctrl_c=True):
#    """
#    Creates and launches a process. 
#
#    Uses subprocess to launch a process. Blocking.
#    When called, might throw a OSError or ValueError.
#    Throws a ChildKilledError if ctrl-C is pressed.
#    """
#    global VERBOSE
#    retcode = None
#    environment = {}
#    environment.update(os.environ)
#    environment.update(variables_dict)
#    try:
#        if VERBOSE:
#            print("--------")
#        print("COMMAND: %s" % (command_str))
#        p = subprocess.Popen(command_str, shell=True, env=environment)
#        print("PID: %s" % (p.pid))
#        if VERBOSE:
#            print("ENV: %s" % (str(variables_dict)))
#            print("--------")
#        retcode = p.wait() # blocking
#        if retcode < 0:
#            err = "Child was terminated by signal %d\n" % (retcode)
#            sys.stderr.write(err)
#        else:
#            err = "Child returned %s\n" % (retcode)
#            sys.stderr.write(err)
#    except OSError, e:
#        err = "Execution of child failed: %s\n" % (e.message)
#        sys.stderr.write(err)
#        retcode = 1
#    except KeyboardInterrupt, e:
#        if die_on_ctrl_c:
#            print("Ctrl-C has been pressed in a slave terminal. Dying.")
#            sys.exit(1)
#        else:
#            raise ChildKilledError("Ctrl-C has been pressed in the master's terminal and caught by a worker.")
#    except ValueError, e:
#        err = "Wrong arguments to subprocess.Popen: %s\n" % (e.message)
#        sys.stderr.write(err)
#        raise
#    #else:
#        #print("Success\n") # retrcode is p.wait() return val
#    return retcode

class PureData(object):
    """
    Launches Pure Data software. 
    """
    def __init__(self, rate=48000, listdev=True, inchannels=2, outchannels=2, verbose=True, driver="jack", nogui=False, blocking=True, patch=None, process_tool="subprocess"):
        global DYNAMIC_PATCH
        self.rate = rate
        self.listdev = listdev
        self.inchannels = inchannels
        self.outchannels = outchannels
        self.verbose = verbose
        self.driver = driver
        self.nogui = nogui
        self.blocking=blocking
        self.patch = patch
        if self.patch is None: # default patch:
            self.patch = DYNAMIC_PATCH
        self.process_tool = process_tool
        self._process_manager = None
        # ready to go

    def start(self):
        """
        Creates args and start pd.
        
        Returns True
        Blocking.
        """
        command = "pd"
        if self.driver == "jack":
            command += " -jack"
        if self.verbose:
            command += " -verbose"
        command += " -r %d" % (self.rate)
        command += " -inchannels %d" % (self.inchannels)
        command += " -outchannels %d" % (self.outchannels)
        command += " %s" % (self.patch)
        #print("Using process tool %s" % (self.process_tool))
        if self.process_tool == "subprocess":
            run_command(command, variables_dict={}, die_on_ctrl_c=True)
            #return True 
            return defer.succeed(True) # right now
        elif self.process_tool == "manager":
            #TODO: env vars
            self._process_manager = process.ProcessManager(
                name="puredata", 
                command=command.split(),
                verbose=True
                )
            d = self._process_manager.start() # deferred
            # print("process manager deferred: %s" % (d))
            return d
        else:
            raise NotImplementedError("no such process tool")
        
    def stop(self):
        raise NotImplementedError("This is still to be done.")

#def fork_and_start_pd(**kwargs):
#    """
#    Please exit the program if pid value is 0 
#    We return the pid 
#    """
#    pid = os.fork()
#    if pid == 0: # child
#        pd = PureData(**kwargs)
#        success = pd.start() # a deferred
#        return 0
#    else: # parent
#        return pid

def run_pd_manager(**kwargs):
    """
    Returns a Deferred.
    Creates a twisted ProcessProtocol for Pure Data.
    """
    def _success(result, _pd):
        #print("Success. This should be a purity client: %s" % (result))
        #return result # pass it to next callback
        return _pd # pass the PureData Manager to the next callback
    def _failure(reason):
        #print(reason.getErrorMessage())
        return reason # pass it to next errback
    #print("starting as a manager")
    _pd = PureData(process_tool="manager", **kwargs)
    d = _pd.start()
    d.addCallback(_success, _pd)
    d.addErrback(_failure)
    #print("pd manager deferred: %s" % (d))
    return d

