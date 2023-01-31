#!/usr/bin/python3

# tests for digimarquee.Slideshow class

import logging, glob, time, multiprocessing, io
from digimarquee import Slideshow, log

log.setLevel(logging.DEBUG)

def test_slideshow():
    '''test that slideshow exits gracefully when terminated'''
    
    sl = Slideshow()
    imagePaths = glob.glob('./media/mame/*.png')
    imagePaths += ['./media/default.png']   
    sl.run(imgPaths = imagePaths)
   
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



if __name__ == '__main__':
    test_slideshow()
