#!/usr/bin/python3

# tests for dynquee.Slideshow class

import logging, logging.config, glob, time, io, os, threading
from dynquee import Slideshow, log, config

log.setLevel(logging.DEBUG)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_dynquee.ini" % os.path.dirname(__file__)
    config.read(configFile)
    log.info("loaded test config file: %s" % configFile)
    # use live media dir to test
    config.set('media', 'media_path', './media')



def test_slideshowExit():
    '''test that slideshow exits gracefully when terminated'''
    log.info('')
    sl = Slideshow()
    imagePaths = glob.glob('./media/**/*.png')
    sl.setMedia(imagePaths)
    # capture output
    out = io.StringIO()   
    # count seconds: should reach 40 before loop exits
    for c in range(1, 41):
        log.info('sleeping %d', c)
        out.write('sleeping %d\n' % c)
        time.sleep(1)
        if c == 25:
            # end slideshow thread after 25s
            sl.stop()
    log.info('finished')
    out.flush()
    # check we reached 40 before loop ended
    assert out.getvalue().endswith('sleeping 40\n'), f"output:\n{out.getvalue()}"
    del(sl)


def test_slideshow():
    log.info('')
    sl = Slideshow()
    imagePaths = glob.glob('./media/**/*')
    sl.setMedia(imagePaths)
    time.sleep(60)
    sl.stop()  
    del(sl)


def test_slideshow1File():
    log.info('')
    sl = Slideshow()
    imagePaths = ['./media/default.png']
    sl.setMedia(imagePaths)
    time.sleep(10)
    sl.stop()
    del(sl)


def test_slideshowMediaChange():
    log.info('')
    sl = Slideshow()
    imagePaths = ['./media/default.png', './tests/media/generic/1MinCountdown.mp4']
    sl.setMedia(imagePaths)
    print("sleeping 10s")
    time.sleep(10)
    print("changing media set")
    sl.setMedia(['./media/default.png'])
    sl._mediaChange.set()
    time.sleep(10)
    sl.stop()
    del(sl)



if __name__ == '__main__':
    setupTestConfig()
    test_slideshow1File()
    test_slideshow()
    test_slideshowExit()
    test_slideshowMediaChange()

    # report threads on exit: should only be MainThread
    time.sleep(1)
    print(f"threads remaining: {threading.enumerate()}")
    assert len(threading.enumerate()) == 1, f"expected only MainThread"
