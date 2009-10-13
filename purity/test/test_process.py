#!/usr/bin/env python 
# -*- coding: utf-8 -*-
"""
Unit tests for miville.streams.conf and miville.streams.milhouse
Streams configuration and actual streaming. 
"""
import os
import pprint
import warnings

from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import failure
import zope.interface

from purity import process

VERBOSE = False
#VERBOSE = True
#MOVIEFILENAME = "/var/tmp/excerpt.ogm"
MOVIEFILENAME = "/var/tmp/purity_test_mplayer.mov"

from twisted.internet import base
base.DelayedCall.debug = True

class Test_02_Asynchronous(unittest.TestCase):
    """
    tests the DeferredWrapper and DelayedWrapper
    """
    def test_01_deferred(self):
        def _later(wrapper):
            wrapper.callback(True)
        wrapper = process.DeferredWrapper()
        deferred = wrapper.make_deferred()
        reactor.callLater(0.01, _later, wrapper)
        return deferred

    def test_02_later(self):
        def _later(test_case, arg2, kwarg1=None):
            if arg2 != "arg2":
                test_case.fail("Arg #2 should be \"arg2\".")
            if kwarg1 != "kwarg1":
                test_case.fail("KW Arg #1 should be \"kwarg1\".")
            return True
        def _callback(result, test_case):
            if result is not True:
                test_case.fail("Result should be True.")
        delayed = process.DelayedWrapper()
        deferred = delayed.call_later(0.01, _later, self, "arg2", kwarg1="kwarg1")
        deferred.addCallback(_callback, self)
        return deferred
    
    def test_03_cancel_call_later(self):
        def _later(test_case):
            test_case.fail("_later should never have been called.")
            return fail.Failure(Exception("This should never be called"))
        def _callback(result, test_case):
            if result != "Cancelled":
                test_case.fail("Result should be the string \"cancelled\".")
        delayed = process.DelayedWrapper()
        deferred = delayed.call_later(0.1, _later, self)
        deferred.addCallback(_callback, self)
        delayed.cancel("Cancelled")
        return deferred

    def test_04_deferred_list(self):
        def _cb(result, self):
            #print("overall success:")
            #print(result)
            return result
        def _eb(reason, self):
            # reason should be a failure.
            #print("overall failure:")
            #print(reason.getErrorMessage())
            return True
        #print("creating deferreds")
        l = []
        a = defer.Deferred()
        b = defer.Deferred()
        l.append(a)
        l.append(b)
        #l.append(defer.succeed(True))
        #l.append(defer.fail(failure.Failure(Exception("error"))))
        #print("creating dl wrapper")
        d = process.deferred_list_wrapper(l)
        d.addCallback(_cb, self)
        d.addErrback(_eb, self)
        #print("trigger the callback")
        a.callback(True)
        #print("trigger the errback")
        b.errback(Exception("Errrororo message"))
    
_globals_04 = {}
class Test_04_Process_Manager(unittest.TestCase):
    """
    Tests the ProcessManager
    """
    def setUp(self):
        global _globals_04
        self.globals = _globals_04

    def XXtest_01_start(self):
        def _callback(result, test_case):
            return test_case.globals["manager"].stop()
        kwargs = {
            "command":["xlogo"],
            }
        self.globals["manager"] = process.ProcessManager(**kwargs)
        deferred = self.globals["manager"].start()
        deferred.addCallback(_callback, self)
    
    def test_04_start_and_stop_mplayer(self):
        """
        Mplayer process using twisted and JACK.
        """
        def _stop_callback(result, deferred):
            deferred.callback(True)
            return True

        def _stop_err(err, deferred):
            #print("ERROR %s" % (err))
            #return True
            deferred.errback(err)
            return True #return err
            
        def _later(deferred, manager):
            deferred2 = manager.stop()
            deferred2.addCallback(_stop_callback, deferred)
            deferred2.addErrback(_stop_err, deferred)
            #deferred2.callback()
            #deferred.callback(deferred2)
            
        def _start_err(err, manager):
            # stops reactor in case of error starting process
            #print("ERROR %s" % (err))
            #reactor.stop()
            #return True
            return err

        def _start_callback(result, manager):
            DURATION = 2.0
            deferred = defer.Deferred()
            reactor.callLater(DURATION, _later, deferred, manager)
            # stops the process
            #print(str(result))
            #deferred.addCallback(_stop)
            #return True #
            return deferred
        global MOVIEFILENAME
        if not os.path.exists(MOVIEFILENAME):
            warnings.warn("File %s is needed for this test." % (MOVIEFILENAME))
        else:
            # starts the process
            #manager = process.ProcessManager(name="xeyes", command=["xeyes"])
            #  "-vo", "gl2",
            manager = process.ProcessManager(name="mplayer", command=["mplayer", "-ao", "jack", MOVIEFILENAME])
            deferred = manager.start()
            deferred.addCallback(_start_callback, manager)
            deferred.addErrback(_start_err, manager)
            return deferred

    def test_03_start_and_stop_sleep_that_dies(self):
        """
        Catches when the process dies.
        """
        def _stop_callback(result, deferred, test_case):
            global _globals_04
            # XXX: calling stop() when done doesnt give any error anymore
            #if result != "NO ERROR DUDE":
            #    msg = "The process was still running and has been killed succesfully... Stop() should have created an error."
            #    fail = failure.Failure(Exception(msg))
            #    deferred.errback(fail)
            #    #test_case.fail(msg) # for some reason this doesn;t work, since we returned a deferred ! IMPORTANT
            
            if not _globals_04["obs"].called:
                raise Exception("Observer never called !!")
            return True
                #return fail

        def _stop_err(err, deferred, test_case):
            # That's what wer expected
            deferred.callback(True)
            #deferred.errback(err)
            return "NO ERROR DUDE" #return err
            #return err
            
        def _later(deferred, manager, test_case):
            deferred2 = manager.stop()
            deferred2.addErrback(_stop_err, deferred, test_case) # order matters ! this first.
            deferred2.addCallback(_stop_callback, deferred, test_case)
            
        def _start_err(err, manager, test_case):
            return err

        def _start_callback(result, manager, test_case):
            DURATION = 4.0
            deferred = defer.Deferred()
            reactor.callLater(DURATION, _later, deferred, manager, test_case)
            return deferred
        
        # starts the process
        manager = process.ProcessManager(name="sleep", command=["sleep", "2"])
        deferred = manager.start()
        deferred.addCallback(_start_callback, manager, self)
        deferred.addErrback(_start_err, manager, self)
        return deferred # only possible to fail it by calling deferred.errback() !! 

    test_03_start_and_stop_sleep_that_dies.skip = "Heavy changes in process management so this test must be updated."
    
    def test_01_executable_not_found(self):
        try:
            manager = process.ProcessManager(name="dummy", command=["you_will_not_find_me"])
        except process.ManagedProcessError:
            pass
        else:
            self.fail("Should have thrown error since executable not possible to find.")

    def test_02_start_and_stop_xeyes(self):
        """
        xeyes process using twisted
        """
        def _stop_callback(result, deferred):
            deferred.callback(True)
            return True
        def _stop_err(err, deferred):
            deferred.errback(err)
            return True #return err
        def _later(deferred, manager):
            deferred2 = manager.stop()
            deferred2.addCallback(_stop_callback, deferred)
            deferred2.addErrback(_stop_err, deferred)
        def _start_err(err, manager):
            return err
        def _start_callback(result, manager):
            DURATION = 2.0
            deferred = defer.Deferred()
            reactor.callLater(DURATION, _later, deferred, manager)
            return deferred
            
        # starts the process
        global _globals_04
        #obs = DummyObserver(self)
        #_globals_04["obs"] = obs # XXX Needs to be a global since observer uses a weakref !!!
        manager = process.ProcessManager(name="xeyes", command=["xeyes", "-geometry", "640x480"])
        #obs.append(manager.subject)
        #print(manager.subject.observers.values())
        #d = manager.subject.observers
        #for v in d.itervalues():
        #    print v
            #print("Subjects:" + str(manager.subject.observers))
        deferred = manager.start()
        deferred.addCallback(_start_callback, manager)
        deferred.addErrback(_start_err, manager)
        return deferred

