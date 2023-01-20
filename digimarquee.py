#!/usr/bin/python

import subprocess, signal, logging, os, glob, random

# for testing:
import time


# Logging setup
def getLogger(logLevel, **kwargs):
    '''Script logger
        :param int logLevel: events at this level or more serious will be logged
    '''
    logging.basicConfig(
        format = '%(asctime)-15s %(levelname)-7s %(funcName)s():%(lineno)d %(message)s',
        datefmt = '%H:%M:%S',
        level = logLevel,
        **kwargs
    )
    return logging.getLogger(__name__)

# Should eventually log to /recalbox/share/system/logs/ ?
log = getLogger(logging.DEBUG);



class ChildProcessManager(object):
    '''Manages a connection to a single child process. Handles failure to launch & unexpected exit gracefully.
    '''

    def __init__(self):
        self._childProcess = None
        "reference to child process: instance of subprocess.Popen"

        # handle exit of child process gracefully
        for sig in [signal.SIGCHLD, signal.SIGPIPE]:
            signal.signal(sig, self._childProcessEnded)

    def __del__(self):
        '''Terminate any running child process before shutdown'''
        if self._childProcess is not None:
            log.info("terminating child process before shutdown")
            self._childProcess.terminate()


    def _launchChild(self, cmdline, **kwargs):
        '''Launch a child process.
            :param str[] cmd: list of commandline parts to pass to subprocess.Popen
        '''
        self._childProcess = subprocess.Popen(
            cmdline,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            **kwargs
        )
        log.debug(
            "launch %s pid=%d",
            ' '.join(cmdline),
            self._childProcess.pid
        )

    def _childProcessEnded(self, signum, _):
        '''Called when the child process fails to launch or exits.
            :returns: a tuple containing output from child process: stdout, stderr
        '''
        log.debug("received signal %d", signum)
        stdout, stderr = None, None
        if self._childProcess is not None:
            # catch any output and log it
            stdout, stderr = self._childProcess.communicate()
            log.info(
                "child process exited with code %d\nstdout:%s\n\nstderr:%s\n",
                self._childProcess.returncode,
                stdout,
                stderr
            )
            # clear reference to subprocess
            self._childProcess = None
        return stdout, stderr



class RecalboxMQTTSubscriber(ChildProcessManager):
    '''MQTT subscriber: handles connection to mosquitto_sub, receives events from EmulationStation'''

    MQTT_CLIENT = './announce_time.sh' # for testing, really 'mosquitto_sub'
    MQTT_CLIENT_OPTS = [
        '-h', '127.0.0.1',
        '-p', '1883',
        '-q', '0',
        '-t', 'Recalbox/EmulationStation/Event'
    ]

    def start(self, *args):
        self._launchChild(
            [self.MQTT_CLIENT] + self.MQTT_CLIENT_OPTS + list(args),
            bufsize = 4096
        )

    def getEvent(self):
        '''Read an event from the MQTT server (blocks until data is received)
            :returns: str an event from the MQTT server, or None if the server terminated
        '''
        try: 
            line = self._childProcess.stdout.readline()
            return line
        except IOError as e:
            # IOError if child process terminates while we're waiting for it to send output
            log.warn("IOError while waiting for output from child process: %s", e)
            return None



class RecalboxEventHandler(object):
    
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

    #MARQUEE_BASE_PATH = '/recalbox/share/digimarquee/media'

    #for testing:
    MARQUEE_BASE_PATH = '/net/bungle/chris/projects/Retrocade_2022/recalbox/media'
    "path where marquee media files are located"

    # PLAYER = '/usr/bin/mpv'
    # for testing:
    PLAYER = '/usr/bin/cvlc'
    "path to media player executable"
    
    PLAYER_OPTS = ['--loop'] #["--vo=drm", "--drm-connector=1.HDMI-A-2", "--hwdec=mmal", "--loop"]
    "options passed to media player executable"


    def _getMediaMatching(self, globPattern):
        '''Search for media files matching globPattern under MARQUEE_BASE_PATH. If >1 found return one at random.
            :returns: path of a matching file, or None
        '''
        log.debug("searching for media files matching %s", globPattern)
        files = glob.glob("%s/%s" % (self.MARQUEE_BASE_PATH, globPattern))
        log.debug("found %d files: %s", len(files), files)
        if len(files) == 0:
            return None
        else:
            return random.choice(files)


    def getMedia(self, action, systemId, gamePath, actionData='', publisher='', genre='', imagePath=''):
        '''Work out which media file to display on the marquee
            Precedence:
            1. ROM-specific media file (if browsing or playing a game)
            2. publisher media file
            3. genre media file
            4. system media file
            5. generic file
            6. default logo
        '''
        # get game filename without directory and extension (only last extension removed)
        gameBasename = os.path.splitext(os.path.basename(gamePath))[0]
        log.debug("gameBasename=%s", gameBasename)
        
        # TODO: do we even need named categories here? only useful for logging
        precedence = [
            ('rom', "%s/%s.*" % (systemId, gameBasename)),
            ('publisher', "publisher/%s.*" % publisher),
            ('genre', "genre/%s.*" % genre), # genre may need special handling: split on comma/slash, partial matching?
            ('system', "system/%s.*" % systemId),
            ('generic', "generic/*")
        ]
        # find best matching media file for game
        for cat, globPattern in precedence:
            log.debug("cat=%s, globPattern=%s", cat, globPattern)
            # try finding media file for this category
            file = self._getMediaMatching(globPattern)
            if file is not None:
                return file 
        # if no other suitable file, found return the default image
        return 'default.png'


    def showOnMarquee(self, filepath, *args):
        '''Display a still image or video clip on the marquee.
            :param str filepath: to path to the media file to display
            :param Any args: any additional args to pass to the media player
        '''
        # terminate running media player if any
        if self._childProcess is not None:
            self._childProcess.terminate()
        # launch player to display media
        self._launchChild(
            [self.PLAYER] + self.PLAYER_OPTS + [filepath] + list(args)
        )





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
    # mm.showOnMarquee('./media/mame/asteroid.png')
    # print(mm.getMediaForROM('mame', 'chasehq'))
    # print(mm.getMediaForROM('mame', 'ffight'))
    # print(mm.getMediaForROM('mame', 'asteroid'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/chasehq.zip', publisher='Taito'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/_.zip', publisher='Taito'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/_.zip', genre='Driving'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='unknown', gamePath=''))


if __name__ == '__main__':
    # testRecalboxMQTTSubscriber()
    testMediaManager()

    # TODO: investigate why prog exits immediately when cvlc killed

    # log.debug('sleep(10)')
    # time.sleep(10)

log.info("end of program")
