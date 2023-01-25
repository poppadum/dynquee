#!/usr/bin/python

# tests for digimarquee.MediaManager class

import os, time, threading, StringIO
from digimarquee import MediaManager, log, config


def __killProcess(process):
    log.debug("killing process pid %d", process.pid)
    process.kill()


def test_playerKilled():
    '''test that program continues if media player process unexpectedly terminates'''
    
    mm = MediaManager()
    config.read('%s/test_digimarquee.config.txt' % os.path.dirname(__file__))
    mm.show('./media/default.png')
    
    # capture output
    out = StringIO.StringIO()
    # thread to kill media player process after 5s
    killer = threading.Timer(5.0, __killProcess, args=(mm._subprocess,))
    killer.start()
    # count seconds: should reach 10 before loop exits
    for c in range(1, 11):
        log.debug('sleeping %d', c)
        out.write('sleeping %d\n' % c)
        time.sleep(1)
    log.debug('finished')
    out.flush()

    # check we reached 10 before loop ended
    assert out.getvalue().endswith('sleeping 10\n'), "output:\n%s" % out.getvalue()


if __name__ == '__main__':
    test_playerKilled()
