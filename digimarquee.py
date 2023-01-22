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
        format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)d %(message)s',
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
        self._terminateChild()


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


    def _terminateChild(self):
        '''Terminate any running child process'''
        if self._childProcess is not None:
            log.info("terminating child process")
            self._childProcess.terminate()


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



class MQTTSubscriber(ChildProcessManager):
    '''MQTT subscriber: handles connection to mosquitto_sub, receives events from EmulationStation
        and reads event params from event file
    '''

    _MQTT_CLIENT = 'mosquitto_sub'
    _MQTT_CLIENT_OPTS = [
        '-h', '127.0.0.1',
        '-p', '1883',
        '-q', '0',
        '-t', 'Recalbox/EmulationStation/Event'
    ]

    _ES_STATE_FILE = 'test/es_state.inf'
    "path to EmulationStation's state file"


    def start(self, *args):
        '''Start the MQTT client; pass *args to the command line'''
        self._launchChild(
            [self._MQTT_CLIENT] + self._MQTT_CLIENT_OPTS + list(args),
            bufsize = 4096
        )

    def stop(self):
        '''Request the MQTT client process to terminate'''
        self._terminateChild()


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


    def getEventParams(self):
        '''Read event params from ES state file, stripping any CR characters
            :returns dict: a dict mapping param names to their values
        '''
        params = {}
        with open(self._ES_STATE_FILE, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                log.debug("key=%s value=%s" % (key, value))
                params[key] = value
        return params
    


class MediaManager(ChildProcessManager):
    '''Finds appropriate media files for a system or game and manages connection to the media player executable
    '''

    #_MARQUEE_BASE_PATH = '/recalbox/share/digimarquee/media'
    #for testing:
    _MARQUEE_BASE_PATH = '/net/bungle/chris/projects/Retrocade_2022/recalbox/media'
    "path where marquee media files are located"

    # PLAYER = '/usr/bin/mpv'
    # for testing:
    _PLAYER = '/usr/bin/cvlc'
    "path to media player executable"

    #_PLAYER_OPTS = ["--vo=drm", "--drm-connector=1.HDMI-A-2", "--hwdec=mmal", "--loop"]
    #for testing:
    _PLAYER_OPTS = ['--loop']
    "options passed to media player executable"


    # Precedence rules: which order to search for media files
    #   depending on EmulationStation's action
    #
    #   rom: ROM-specific media file
    #   publisher: publisher media file
    #   genre: genre media file
    #   system: system media file
    #   generic: a media file unrelated to a game, system or publisher
    #   scraped: game's scraped image
    _PRECEDENCE = {
        'gamelistbrowsing': ['rom', 'scraped', 'publisher', 'system', 'genre', 'generic'],
        'systembrowsing': ['system', 'generic'],
        # default precedence to use if action does not match one of those above
        'default': ['generic'],
    }


    # Glob patterns to find media files for each search type
    _GLOB_PATTERNS = {
        'rom': "%(systemId)s/%(gameBasename)s.*",
        'publisher': "publisher/%(publisher)s.*",
        'genre': "genre/%(genre)s.*",
        'system': "system/%(systemId)s.*",
        'generic': "generic/*"
    }


    def _getMediaMatching(self, globPattern):
        '''Search for media files matching globPattern under MARQUEE_BASE_PATH. If >1 found return one at random.
            :returns: path of a matching file, or None
        '''
        log.debug("searching for media files matching %s", globPattern)
        files = glob.glob("%s/%s" % (self._MARQUEE_BASE_PATH, globPattern))
        log.debug("found %d files: %s", len(files), files)
        if len(files) == 0:
            return None
        else:
            return random.choice(files)


    def getMedia(self, action, systemId, gamePath, actionData='', publisher='', genre='', imagePath=''):
        '''Work out which media file to display on the marquee using the precedence rules for the action
            :returns: str path to a media file
        '''
        # get game filename without directory and extension (only last extension removed)
        gameBasename = os.path.splitext(os.path.basename(gamePath))[0]
        log.debug("gameBasename=%s", gameBasename)
        
        # Look up precedence rules for this action
        try:
            precedence = self._PRECEDENCE[action]
        except KeyError:
            # if no rules for this action, use the default rules
            precedence = self._PRECEDENCE['default']

        # find best matching media file for game trying each rule in turn
        for rule in precedence:
            # if using scraped image just return its path
            if rule == 'scraped':
                log.debug("rule=%s imagePath=%s", rule, imagePath)
                if imagePath == '':
                    continue
                else:
                    return imagePath

            globPattern = self._GLOB_PATTERNS[rule] % {
                'gameBasename': gameBasename,
                'systemId': systemId.lower(),
                'publisher': publisher.lower(),
                'genre': genre.lower(),
            }
            log.debug("rule=%s globPattern=%s", rule, globPattern)
            # try finding media file matching this glob pattern
            file = self._getMediaMatching(globPattern)
            if file is not None:
                # if a matching file was found, stop searching and return it
                return file 
        # if no other suitable file, found return the default image
        return '%s/default.png' % self._MARQUEE_BASE_PATH


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
            [self._PLAYER] + self._PLAYER_OPTS + [filepath] + list(args)
        )




def testMediaManager():
    mm = MediaManager()
    # mm.showOnMarquee('./media/mame/asteroid.png')
    # print(mm.getMediaForROM('mame', 'chasehq'))
    # print(mm.getMediaForROM('mame', 'ffight'))
    # print(mm.getMediaForROM('mame', 'asteroid'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/chasehq.zip', publisher='Taito'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/_.zip', publisher='Taito'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='mame', gamePath='/recalbox/share_init/roms/mame/_.zip', genre='Driving', imagePath='/path/to/scraped_image'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='UNKNOWN', gamePath='/recalbox/share_init/roms/_/UNKNOWN.zip', genre='Shooter'))
    print(mm.getMedia(action='gamelistbrowsing', systemId='UNKNOWN', gamePath=''))




if __name__ == '__main__':
    testMediaManager()

    # TODO: investigate why prog exits immediately when cvlc killed

    # log.debug('sleep(10)')
    # time.sleep(10)

log.info("end of program")
