#!/usr/bin/python

import subprocess, signal, logging, os, glob, random, ConfigParser

def getLogger(logLevel, **kwargs):
    '''Module logger
        :param int logLevel: events at this level or more serious will be logged
        :returns: an instance of logging.Logger
    '''
    logging.basicConfig(
        format = '%(asctime)s %(levelname)s %(funcName)s():%(lineno)d %(message)s',
        datefmt = '%H:%M:%S',
        level = logLevel,
        **kwargs
    )
    return logging.getLogger(__name__)


# Module config file
_CONFIG_FILE = "digimarquee.config.txt"

def loadConfig():
    '''Load config file into ConfigParser instance and return it.
        Search order:
        1. /boot
        2. module directory
        3. current directory
    '''
    config = ConfigParser.ConfigParser()
    _configFilesRead = config.read([
        "/boot/%s" % _CONFIG_FILE,
        "%s/%s" % (os.path.dirname(__file__), _CONFIG_FILE),
        _CONFIG_FILE
    ])
    log.info("loaded config file(s): %s", _configFilesRead)
    return config



class ProcessManager(object):
    '''Manages a connection to a single subprocess. Handles failure to launch & unexpected exit gracefully.
    '''

    def __init__(self):
        self._subprocess = None
        "reference to subprocess (instance of subprocess.Popen)"

        # handle exit of subprocess gracefully
        signal.signal(signal.SIGCHLD, self._subprocessEnded)

    def __del__(self):
        '''Terminate any running subprocess before shutdown'''
        self._terminate()


    def _launch(self, cmdline, **kwargs):
        '''Launch a subprocess
            :param str[] cmdline: list of commandline parts to pass to subprocess.Popen
            :param **kwargs: additional args to pass to subprocess.Popen
        '''
        self._subprocess = subprocess.Popen(
            cmdline,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            **kwargs
        )
        log.debug("cmd=%s pid=%d", cmdline, self._subprocess.pid)


    def _terminate(self):
        '''Terminate subprocess if running'''
        if self._subprocess is not None:
            log.debug("terminating subprocess pid=%d", self._subprocess.pid)
            self._subprocess.terminate()


    def _subprocessEnded(self, signum, _):
        '''Called when the subprocess fails to launch or exits: capture output & return code and log it'''
        log.debug("received signal %d", signum)
        if self._subprocess is not None:
            # capture return code & output and log it
            stdout, stderr = self._subprocess.communicate()
            rc = self._subprocess.returncode if self._subprocess is not None else None
            log.debug("subprocess exited with code %s\nstdout:%s\n\nstderr:%s", rc, stdout, stderr)
            # clear reference to subprocess
            self._subprocess = None



class MQTTSubscriber(ProcessManager):
    '''MQTT subscriber: handles connection to mosquitto_sub, receives events from EmulationStation
        and reads event params from event file
    '''

    _CONFIG_SECTION = 'recalbox'
    "config file section for MQTTSubscriber"


    def start(self, *args):
        '''Start the MQTT client; pass *args to the command line'''
        self._launch(
            [config.get(self._CONFIG_SECTION, 'MQTT_CLIENT')] + config.get(self._CONFIG_SECTION, 'MQTT_CLIENT_OPTS').split() + list(args),
            bufsize = 4096
        )

    def stop(self):
        '''Request the MQTT client process to terminate'''
        self._terminate()


    def getEvent(self):
        '''Read an event from the MQTT client (blocks until data is received)
            :returns str: an event from the MQTT client, or None if the client terminated
        '''
        try: 
            return self._subprocess.stdout.readline().strip()
        except IOError as e:
            # IOError if child process terminates while we're waiting for it to send output
            log.warn("IOError while waiting for output from child process: %s", e)
            return None


    def getEventParams(self):
        '''Read event params from ES state file, stripping any CR characters
            :returns dict: a dict mapping param names to their values
        '''
        params = {}
        with open(config.get(self._CONFIG_SECTION, 'ES_STATE_FILE')) as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                log.debug("key=%s value=%s" % (key, value))
                params[key] = value
        return params
    


class MediaManager(ProcessManager):
    '''Finds appropriate media files for an EmulationStation action and manages connection to the media player executable
    '''

    _CONFIG_SECTION = 'media'
    "config file section for MediaManager"


    # Glob patterns to find media files for each search rule
    # Valid search rules:
    #   rom: ROM-specific media file
    #   publisher: publisher media file
    #   genre: genre media file
    #   system: system media file
    #   generic: a media file unrelated to a game, system or publisher
    #   scraped: game's scraped image
    _GLOB_PATTERNS = {
        'rom': "%(systemId)s/%(gameBasename)s.*",
        'publisher': "publisher/%(publisher)s.*",
        'genre': "genre/%(genre)s.*",
        'system': "system/%(systemId)s.*",
        'generic': "generic/*"
    }


    def __init__(self):
        '''Override constructor to add currentMedia property'''
        super(MediaManager, self).__init__()
        self._currentMedia = None
        "path to media file currently displayed, or None"
    

    def _getMediaMatching(self, globPattern):
        '''Search for media files matching globPattern under BASE_PATH. If >1 found return one at random.
            :returns str: path of a matching file, or None
        '''
        log.debug("searching for media files matching %s", globPattern)
        files = glob.glob("%s/%s" % (config.get(self._CONFIG_SECTION, 'BASE_PATH'), globPattern))
        log.debug("found %d files: %s", len(files), files)
        if files == []:
            return None
        else:
            return random.choice(files)


    def getMedia(self, precedence, params):
        '''Work out which media file to display on the marquee using precedence rules
            :params list[str] precedence: ordered list of search rules to try in turn
            :param dict[str,str] params: a dict of event parameters
            :returns str: path to a media file
        '''
        log.debug("precedence=%s params=%s", precedence, params)
        # get game filename without directory and extension (only last extension removed)
        gameBasename = os.path.splitext(os.path.basename(params.get('gamePath', '')))[0]
        log.debug("gameBasename=%s", gameBasename)
        
        # find best matching media file for game, trying each rule in turn
        for rule in precedence:
            # if using scraped image just return its path
            if rule == 'scraped':
                imagePath = params.get('imagePath', '')
                log.debug("rule=%s imagePath=%s", rule, imagePath)
                if imagePath == '':
                    # skip rule if no scraped image exists
                    continue
                else:
                    return imagePath
            # skip unrecognised rules
            if rule not in self._GLOB_PATTERNS:
                log.warning("skipped unrecognised rule name '%s'", rule)
                continue
            # insert event params into rule's glob pattern
            globPattern = self._GLOB_PATTERNS[rule] % {
                'gameBasename': gameBasename,
                'systemId': params.get('systemId', '').lower(),
                'publisher': params.get('publisher', '').lower(),
                'genre': params.get('genre', '').lower(),
            }
            log.debug("rule=%s globPattern=%s", rule, globPattern)
            # try finding media file matching this glob pattern
            file = self._getMediaMatching(globPattern)
            if file is not None:
                # if a matching file was found, stop searching and return it
                return file 
        # if no other suitable file, found return the default image
        return '%s/default.png' % config.get(self._CONFIG_SECTION, 'BASE_PATH')


    def show(self, filepath, *args):
        '''Display a still image or video clip on the marquee.
            :param str filepath: to path to the media file to display
            :param Any args: any additional args to pass to the media player
        '''
        # if we're already showing the media file, do nothing
        if filepath == self._currentMedia:
            log.debug("already showing %s" % filepath)
            return
        # terminate running media player if any
        self._terminate()
        # launch player to display media
        self._launch(
            [config.get(self._CONFIG_SECTION,'PLAYER')] + config.get(self._CONFIG_SECTION, 'PLAYER_OPTS').split() + [filepath] + list(args)
        )
        self._currentMedia = filepath


    def clear(self):
        '''Terminate media player process (if running) to clear marquee'''
        self._terminate()
        self._currentMedia = None



class EventHandler(object):
    '''Receives events from MQTTSubscriber and pass to MediaManager'''

    _CONFIG_SECTION = 'search'
    "config file section for EventHandler"

    
    def __init__(self):
        self._ms = MQTTSubscriber()
        self._ms.start()
        self._mm = MediaManager()


    def readEvents(self):
        '''Read and handle all events from the MQTTSubscriber'''
        while True:
            event = self._ms.getEvent()
            if not event:
                break
            log.debug('event received: %s' % event)
            params = self._ms.getEventParams()
            self._handleEvent(event, params)


    def _getPrecedence(self, action):
        '''Get precedence rules for this action from config file
            :returns list[str]: ordered list of precedence rules'''
        try:
            precedence = config.get(self._CONFIG_SECTION, action).split(',')
        except ConfigParser.NoOptionError:
            # if no rules for this action, use the default rules
            precedence = config.get(self._CONFIG_SECTION, 'default').split(',')
        log.debug("action=%s precedence=%s", action, precedence)
        return precedence


    def _handleEvent(self, action, params):
        '''Find appropriate media file for the event and display it
            :param str event: EmulationStation action 
            :param dict[str,str] params: a dict of event parameters
        '''
        log.debug("action=%s, params=%s", action, params)
        precedence = self._getPrecedence(action)
        mediaPath = self._mm.getMedia(precedence, params)
        # display media file if not already showing
        if mediaPath is not None:
            self._mm.show(mediaPath)



# Logging setup
# TODO: Should eventually log to /recalbox/share/system/logs/ ?
# for now, just log to stderr
log = getLogger(logging.DEBUG)

# Read config file
config = loadConfig()


### main ###

if __name__ == '__main__':
    eh = EventHandler()
    eh.readEvents()
    log.debug('exiting')
