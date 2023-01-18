#!/usr/bin/python

import subprocess, signal, logging, time

# Logging setup
logging.basicConfig(
    format = '%(asctime)-15s %(levelname)-7s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    level = logging.DEBUG
)
log = logging.getLogger(__name__)


# MQTT subscriber
class RecalboxMQTTSubscriber:
    '''MQTT subscriber: handles connection to mosquitto_sub'''

    #_pipe = None
    #"pipe to mosquitto_sub subprocess"

    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)


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
        log.debug("RecalboxMQTTSubscriber.shutdown(%d) requested", args[0])
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
    


class MediaManager:
    '''Finds appropriate media files for a system or game and manages connection to the media player executable
    '''

    PLAYER = '/usr/bin/cvlc'
    "path to media player executable"
    
    PLAYER_OPTS = [] #["--vo=drm", "--drm-connector=1.HDMI-A-2", "--hwdec=mmal", "--loop"]
    "options passed to media player executable"


    def __init__(self):
        self._player = None
        "reference to media player subprocess"

        # handle exit of media player subprocess gracefully
        signal.signal(signal.SIGPIPE, self._playerExited)
        signal.signal(signal.SIGCHLD, self._playerExited)


    def getMarqueeMediaForROM(self, systemId, gameBasename):
        '''Search for ROM-specific media files, and if >1 found, return one at random.
        
        '''

    def showOnMarquee(self, filepath, *args):
        '''Display a still image or video clip on the marquee.
            :param str filepath: to path to the media file to display
            :param Any args: any additional args to pass to the media player
        '''
        # terminate the existing media player if any
        if self._player is not None:
            self._player.terminate()
        
        # launch media player
        try:
            log.debug('launching media player: %s', ' '.join([self.PLAYER] + self.PLAYER_OPTS + [filepath] + list(args) ))
            self._player = subprocess.Popen(
                [self.PLAYER] + self.PLAYER_OPTS + [filepath],
                
                # TODO: log stderr to a file?
                stderr = subprocess.PIPE
            )
        except (OSError, ValueError) as e:
            if self._player is None:
                log.error("could not start media player subprocess: %s", e)
    
 
    def clearMarquee(self):
        '''Terminate any running media player subprocess'''
        if self._player is not None:
            self._player.terminate()
            log.debug("%s.clearMarquee() called: subprocess exited with code %d", __name__, self._player.returncode)


    def _playerExited(self, signum, _):
        '''Called when the media player subprocess fails to launch or exits unexpectedly'''
        # catch any error output and log it
        if self._player is not None:
            _, stderr = self._player.communicate()
            log.error(
                "%s._playerExited(): media player process exited unexpectedly with code %d",
                self.__class__.__name__,
                self._player.returncode
            )
        if stderr is not None:
            log.error(stderr)
        # clear reference to subprocess
        self._player = None



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
    mm.showOnMarquee('./media/mame/asteroid.png', '--version', '--hello')
    time.sleep(5)



if __name__ == '__main__':
    # testRecalboxMQTTSubscriber()
    testMediaManager()

log.info("end of program")
