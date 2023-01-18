#!/usr/bin/python

import subprocess, signal, logging, time

# Logging setup
def getLogger(logLevel, **kwargs):
    '''Script logger
        :param int logLevel: events at this level or more serious will be logged
    '''
    logging.basicConfig(
        format = '%(asctime)-15s %(levelname)-7s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        level = logLevel,
        **kwargs
    )
    return logging.getLogger(__name__)

log = getLogger(logging.DEBUG);


#
# TODO: RecalboxMQTTSubscriber inherit from ChildProcessManager?
#

class ChildProcessManager:
    '''Manages a connection to a single child process. Handles failure to launch & unexpected exit gracefully.
    '''

    def __init__(self):
        self._childProcess = None
        "reference to  child process: instance of subprocess.Popen"

        # handle exit of child process gracefully
        for sig in [signal.SIGCHLD, signal.SIGPIPE]:
            signal.signal(sig, self._childProcessEnded)

    def __del__(self):
        '''Terminate any running child process before shutdown'''
        if self._childProcess is not None:
            log.info("terminating child process before shutdown")
            self._childProcess.terminate()


    def _launchChild(self, *args):
        '''Launch a child process. Subclasses must override this method and set self._childProcess'''
        pass


    def _childProcessEnded(self, signum, _):
        '''Called when the child process fails to launch or exits.
            :returns: a tuple containing output from child process: stdout, stderr
        '''
        log.debug("received signal %d", signum)
        stdout, stderr = None, None
        if self._childProcess is not None:
            # child process terminated unexpectedly so catch any output
            stdout, stderr = self._childProcess.communicate()
            log.info(
                "child process exited unexpectedly with code %d\nstdout:%s\n\nstderr:%s\n",
                self._childProcess.returncode,
                stdout,
                stderr
            )

            # clear reference to subprocess
            self._childProcess = None
        return stdout, stderr




class RecalboxMQTTSubscriber:
    '''MQTT subscriber: handles connection to mosquitto_sub'''

    #_pipe = None
    #"pipe to mosquitto_sub subprocess"

    def __init__(self):
        # handle exit of child process cleanly
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGCHLD, self._shutdown)
        self._pipe = None



    def start(self):
        '''Start the mosquitto_sub subprocess and open a pipe to it'''
        self._pipe = subprocess.Popen(
            [
                './announce_time.sh'
                # 'mosquitto_sub',
                # '-h', '127.0.0.1',
                # '-p', '1883',
                # '-q', '0',
                # '-t', 'Recalbox/EmulationStation/Event'
            ],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            bufsize = 4096
        )
        log.debug("launched mosquitto_sub pid=%d", self._pipe.pid)

    def getEvent(self):
        '''Read an event from the MQTT server (blocks until data is received)'''
        line = self._pipe.stdout.readline()
        return line


    def _shutdown(self, *args):
        '''Terminate the mosquitto_sub subprocess and close the pipe'''
        log.debug(
            "%s.shutdown(%d) requested",
            self.__class__.__name__,
            args[0]
        )
        self._pipe.terminate()



class RecalboxEventHandler:
    
    ES_STATE_FILE = '/tmp/es_state.inf'
    "path to EmulationStation's state file"

    def handleEvent(event):
        '''Take action based on the event
            :param dict event: a dict representing the event with keys: Action, ActionData, SystemId, GamePath, ImagePath
        '''
        


    def getEventParams():
        '''Read event params from ES state file, stripping any CR characters'''
    

class MediaManager(ChildProcessManager):
    '''Finds appropriate media files for a system or game and manages connection to the media player executable
    '''

    # PLAYER = '/usr/bin/mpv'
    # for testing:
    PLAYER = '/usr/bin/cvlc'
    "path to media player executable"
    
    PLAYER_OPTS = ['--loop'] #["--vo=drm", "--drm-connector=1.HDMI-A-2", "--hwdec=mmal", "--loop"]
    "options passed to media player executable"


    def getMarqueeMediaForROM(self, systemId, gameBasename):
        '''Search for ROM-specific media files, and if >1 found, return one at random.
        
        '''

    def showOnMarquee(self, filepath, *args):
        '''Display a still image or video clip on the marquee.
            :param str filepath: to path to the media file to display
            :param Any args: any additional args to pass to the media player
        '''
        self._launchChild(filepath, *args)

    
    def _launchChild(self, filepath, *args):
        # terminate running media player if any
        if self._childProcess is not None:
            self._childProcess.terminate()
        
        # launch media player
        try:
            log.debug('launching media player: %s', ' '.join([self.PLAYER] + self.PLAYER_OPTS + [filepath] + list(args)))
            self._childProcess = subprocess.Popen(
                [self.PLAYER] + self.PLAYER_OPTS + [filepath],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )
        except (OSError, ValueError) as e:
            if self._childProcess is None:
                log.error("could not start media player subprocess: %s", e)





# Test harnesses
def testRecalboxMQTTSubscriber():
    subscriber = RecalboxMQTTSubscriber()
    subscriber.start()
    while True:
        event = subscriber.getEvent()
        if not event:
            break
        log.info("received event: %s", event)


def testMediaManager():
    mm = MediaManager()
    mm.showOnMarquee('./media/mame/asteroid.png')
    time.sleep(15)



if __name__ == '__main__':
    # testRecalboxMQTTSubscriber()
    testMediaManager()

log.info("end of program")
