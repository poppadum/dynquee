#!/usr/bin/env python3

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
    # check we reached 40 before loop ended
    assert out.getvalue().endswith('sleeping 40\n'), f"output:\n{out.getvalue()}"
    out.close()
    del(sl)


def test_slideshow():
    """test slideshow with multiple images for 60s"""
    log.info('')
    sl = Slideshow()
    imagePaths = glob.glob('./media/**/*')
    sl.setMedia(imagePaths)
    time.sleep(60)
    sl.stop()  
    del(sl)


def test_slideshow1File():
    """test slideshow with a single still image"""
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


def test_slideshowVideoFinish():
    log.info('')
    sl = Slideshow()
    imagePaths = ['./tests/media/generic/10sCountdown.mp4', './media/default.png']
    sl.setMedia(imagePaths)
    time.sleep(45)
    sl.stop()
    del(sl)


def test_slideshowMaxVideoTime():
    """test that video stops after max_video_time set in config file"""
    log.info('')
    out = io.StringIO()
    ch = logging.StreamHandler(out)
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)
    sl = Slideshow()
    filePath = './tests/media/generic/1MinCountdown.mp4'
    imagePaths = [filePath]
    sl.setMedia(imagePaths)
    time.sleep(20)
    out.flush()
    sl.stop()
    # check how many times video player launched
    assert out.getvalue().count(filePath) == 6, f"expected 6 occurrences of file in output, got {out.getvalue().count(filePath)}"
    log.removeHandler(ch)
    out.close()
    del(sl)


if __name__ == '__main__':
    setupTestConfig()
    test_slideshow1File()
    test_slideshowExit()
    test_slideshowMediaChange()
    test_slideshowVideoFinish()
    test_slideshowMaxVideoTime()
    test_slideshow()


    # report threads on exit: should only be MainThread
    time.sleep(1)
    print(f"threads remaining: {threading.enumerate()}")
    assert len(threading.enumerate()) == 1, f"expected only MainThread"
