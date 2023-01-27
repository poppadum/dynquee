#!/usr/bin/python3

import subprocess, signal, logging, os, glob, random, io
from configparser import ConfigParser, NoOptionError
from typing import ClassVar, Dict, List, Union

def getLogger(logLevel: int, **kwargs) -> logging.Logger:
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
_CONFIG_FILE: str = "digimarquee.config.txt"

def loadConfig() -> ConfigParser:
    '''Load config file into ConfigParser instance and return it.
        Search order:
        1. /boot
        2. module directory
        3. current directory
    '''
    config: ConfigParser = ConfigParser()
    _configFilesRead: List[str] = config.read([
        f"/boot/{_CONFIG_FILE}",
        f"{os.path.dirname(__file__)}/{_CONFIG_FILE}",
        _CONFIG_FILE
    ])
    log.info(f"loaded config file(s): {_configFilesRead}")
    return config



class ProcessManager(object):
    '''Manages a connection to a single subprocess. Handles failure to launch & unexpected exit gracefully.
    '''

    def __init__(self):
        self._subprocess: subprocess.Popen = None
        "reference to subprocess (instance of subprocess.Popen)"

        self._signum: int = None
        "signal received by subprocess, or None"

        self._pid: int = None
        "pid of subprocess, or None"

        self._hasSubprocessExited = False
        "flag to indicate if subprocess has exited"

        # handle exit of subprocess gracefully
        signal.signal(signal.SIGCHLD, self._subprocessEnded)


    def __del__(self):
        '''Terminate any running subprocess before shutdown'''
        self._terminate()

    @property
    def hasSubprocessExited(self) -> bool:
        return self._hasSubprocessExited


    def _launch(self, cmdline: List[str], **kwargs):
        '''Launch a subprocess
            :param str[] cmdline: list of commandline parts to pass to subprocess.Popen
            :param **kwargs: additional args to pass to subprocess.Popen
        '''
        self._subprocess = subprocess.Popen(
            cmdline,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines = True,
            **kwargs
        )
        self._pid = self._subprocess.pid
        log.debug(f"cmd={cmdline} pid={self._pid}")


    def _terminate(self):
        '''Terminate subprocess if running'''
        if self._subprocess is not None:
            log.debug(f"terminating subprocess pid={self._pid}")
            self._subprocess.terminate()
        self._cleanup()


    def _subprocessEnded(self, signum: int, _):
        '''Called when the subprocess fails to launch or exits: raise exception to be caught in main thread'''
        # record signal received
        self._signum = signum
        self._hasSubprocessExited = True
        signame: str = signal.Signals(signum).name
        log.debug(f'subprocess pid {self._pid} received signal {signame} ({signum})')
    

    def _cleanup(self):
        '''Capture subprocess output and return code; clear reference to subprocess'''
        if self._subprocess is not None:
            log.debug("pid %s received signal %s", self._pid, self._signum)
            # capture return code & output (if any) and log it
            stdout, stderr = None, None
            try:
                stdout, stderr  = self._subprocess.communicate(timeout = 2.0)
            except subprocess.TimeoutExpired:
                pass
            rc: int = self._subprocess.returncode if self._subprocess is not None else None
            log.debug(f"subprocess exited with code {rc}\nstdout:{stdout}\n\nstderr:{stderr}")
            # clear reference to subprocess
            self._subprocess, self._pid, self._signum = None, None, None



class MQTTSubscriber(ProcessManager):
    '''MQTT subscriber: handles connection to mosquitto_sub, receives events from EmulationStation
        and reads event params from event file
    '''

    _CONFIG_SECTION: ClassVar[str] = 'recalbox'
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


    def getEvent(self) -> Union[str, None]:
        '''Read an event from the MQTT client (blocks until data is received)
            :returns str: an event from the MQTT client, or None if the client terminated
        '''
        try: 
            return self._subprocess.stdout.readline().strip()
        except IOError as e:
            # IOError if child process terminates while we're waiting for it to send output
            log.warning(f"IOError while waiting for output from subprocess: {e}")
            return None


    def getEventParams(self) -> Dict[str, str]:
        '''Read event params from ES state file, stripping any CR characters
            :returns dict: a dict mapping param names to their values
        '''
        params: Dict[str,str] = {}
        with open(config.get(self._CONFIG_SECTION, 'ES_STATE_FILE')) as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                log.debug("key=%s value=%s" % (key, value))
                params[key] = value
        return params
    


class MediaManager(ProcessManager):
    '''Finds appropriate media files for an EmulationStation action and manages connection to the media player executable
    '''

    _CONFIG_SECTION: ClassVar[str] = 'media'
    "config file section for MediaManager"


    # Glob patterns to find media files for each search rule
    # Valid search rules:
    #   rom: ROM-specific media file
    #   publisher: publisher media file
    #   genre: genre media file
    #   system: system media file
    #   generic: a media file unrelated to a game, system or publisher
    #   scraped: game's scraped image
    _GLOB_PATTERNS: ClassVar[Dict[str, str]] = {
        'rom': "%(systemId)s/%(gameBasename)s.*",
        'publisher': "publisher/%(publisher)s.*",
        'genre': "genre/%(genre)s.*",
        'system': "system/%(systemId)s.*",
        'generic': "generic/*"
    }


    def __init__(self):
        '''Override constructor to add currentMedia property'''
        super().__init__()
        self._currentMedia: str = None
        "path to media file currently displayed, or None"
    

    def _getMediaMatching(self, globPattern: str) -> Union[str, None]:
        '''Search for media files matching globPattern under BASE_PATH. If >1 found return one at random.
            :returns str: path of a matching file, or None
        '''
        log.debug("searching for media files matching %s", globPattern)
        files: List[str] = glob.glob("%s/%s" % (config.get(self._CONFIG_SECTION, 'BASE_PATH'), globPattern))
        log.debug(f"found {len(files)} files: {files}")
        if files == []:
            return None
        else:
            return random.choice(files)


    def getMedia(self, precedence: List[str], params: Dict[str, str]) -> str:
        '''Work out which media file to display on the marquee using precedence rules
            :params list[str] precedence: ordered list of search rules to try in turn
            :param dict[str,str] params: a dict of event parameters
            :returns str: path to a media file
        '''
        log.debug(f"precedence={precedence} params={params}")
        # get game filename without directory and extension (only last extension removed)
        gameBasename: str = os.path.splitext(os.path.basename(params.get('GamePath', '')))[0]
        log.debug("gameBasename={gameBasename}")
        
        # find best matching media file for game, trying each rule in turn
        for rule in precedence:
            # if using scraped image just return its path
            if rule == 'scraped':
                imagePath: str = params.get('ImagePath', '')
                log.debug(f"rule={rule} ImagePath={imagePath}")
                if imagePath == '':
                    # skip rule if no scraped image exists
                    continue
                else:
                    return imagePath
            # skip unrecognised rules
            if rule not in self._GLOB_PATTERNS:
                log.warning(f"skipped unrecognised rule name '{rule}'")
                continue
            # insert event params into rule's glob pattern
            globPattern: str = self._GLOB_PATTERNS[rule] % {
                'gameBasename': gameBasename,
                'systemId': params.get('SystemId', '').lower(),
                'publisher': params.get('Publisher', '').lower(),
                'genre': params.get('Genre', '').lower(),
            }
            log.debug(f"rule={rule} globPattern={globPattern}")
            # try finding media file matching this glob pattern
            file: Union[str, None] = self._getMediaMatching(globPattern)
            if file is not None:
                # if a matching file was found, stop searching and return it
                return file 
        # if no other suitable file, found return the default image
        return '%s/default.png' % config.get(self._CONFIG_SECTION, 'BASE_PATH')


    def show(self, filepath: str, *args):
        '''Display a still image or video clip on the marquee.
            :param str filepath: to path to the media file to display
            :param Any args: any additional args to pass to the media player
        '''
        # if we're already showing the media file, do nothing
        if filepath == self._currentMedia:
            log.debug(f"already showing {filepath}")
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

    _CONFIG_SECTION: ClassVar[str] = 'search'
    "config file section for EventHandler"

    
    def __init__(self):
        self._ms: MQTTSubscriber = MQTTSubscriber()
        self._ms.start()
        self._mm: MediaManager = MediaManager()


    def readEvents(self):
        '''Read and handle all events from the MQTTSubscriber'''
        while True:
            event: str = self._ms.getEvent()
            if not event:
                break
            log.debug('event received: %s' % event)
            params: Dict[str, str] = self._ms.getEventParams()
            self._handleEvent(params.get('Action'), params)


    def _getPrecedence(self, action: str) -> List[str]:
        '''Get precedence rules for this action from config file
            :returns list[str]: ordered list of precedence rules'''
        try:
            precedence: List[str] = config.get(self._CONFIG_SECTION, action).split(',')
        except NoOptionError:
            # if no rules for this action, use the default rules
            precedence = config.get(self._CONFIG_SECTION, 'default').split(',')
        log.debug(f"action={action} precedence={precedence}")
        return precedence


    def _handleEvent(self, action: str, params: Dict[str, str]):
        '''Find appropriate media file for the event and display it
            :param str event: EmulationStation action 
            :param dict[str,str] params: a dict of event parameters
        '''
        log.debug("action=%s, params=%s", action, params)
        precedence: List[str] = self._getPrecedence(action)
        mediaPath:str  = self._mm.getMedia(precedence, params)
        # display media file if not already showing
        if mediaPath is not None:
            self._mm.show(mediaPath)



# Logging setup
# TODO: Should eventually log to /recalbox/share/system/logs/ ?
# for now, just log to stderr
log: logging.Logger = getLogger(logging.DEBUG)

# Read config file
config: ConfigParser = loadConfig()


### main ###

if __name__ == '__main__':
    eh: EventHandler = EventHandler()
    eh.readEvents()
    log.debug('exiting')
