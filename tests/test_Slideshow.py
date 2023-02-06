#!/usr/bin/python3

# tests for digimarquee.Slideshow class

import logging, glob, time, io, os
from digimarquee import Slideshow, log, config

log.setLevel(logging.DEBUG)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_digimarquee.config.txt" % os.path.dirname(__file__)
    config.read(configFile)
    log.info("loaded test config file: %s" % configFile)



def test_slideshowExit():
    '''test that slideshow exits gracefully when terminated'''
    
    sl = Slideshow()
    imagePaths = glob.glob('./media/mame/*.png')
    imagePaths += ['./media/default.png']   
    sl.run(imagePaths)
   
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
    assert out.getvalue().endswith('sleeping 40\n'), "output:\n%s" % out.getvalue()


def test_slideshow():
    sl = Slideshow()
    imagePaths = glob.glob('./media/mame/*')
    imagePaths += ['./media/default.png']   
    sl.run(imagePaths)
    time.sleep(60)
    sl.stop()


if __name__ == '__main__':
    setupTestConfig()
    test_slideshow()
