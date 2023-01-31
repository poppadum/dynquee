#!/usr/bin/python3

import subprocess, signal, logging, os, glob, random
from configparser import ConfigParser, NoOptionError
from threading import Event
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

        self._pid: int = None
        "pid of subprocess, or None"


    def __del__(self):
        '''Terminate any running subprocess before shutdown'''
        self.terminate()


    def _launch(self, cmdline: List[str], **kwargs):
        '''Launch a subprocess
            :param str[] cmdline: list of commandline parts to pass to subprocess.Popen
            :param **kwargs: additional args to pass to subprocess.Popen
        '''
        try:
            self._subprocess = subprocess.Popen(
                cmdline,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines = True,
                **kwargs
            )
            self._pid = self._subprocess.pid
            log.debug(f"cmd={cmdline} pid={self._pid}")
        except OSError as e:
            log.error(f"unable to launch #{cmdline}: {e}")


    def terminate(self):
        '''Terminate subprocess if running'''
        if self._subprocess is not None:
            log.debug(f"terminating subprocess pid={self._pid}")
            self._subprocess.terminate()
            # capture return code & output (if any) and log it
            stdout, stderr = None, None
            try:
                stdout, stderr  = self._subprocess.communicate(timeout = 2.0)
            except subprocess.TimeoutExpired:
                pass
            rc: int = self._subprocess.wait()
            log.debug(f"subprocess pid={self._pid} exited with code {rc}\nstdout:{stdout}\n\nstderr:{stderr}")
            # clear reference to subprocess
            self._subprocess, self._pid = None, None



class MQTTSubscriber(ProcessManager):
    '''MQTT subscriber: handles connection to mosquitto_sub, receives events from EmulationStation
        and reads event params from event file.

        Usage:
        ```
        start()
        while True:
            event = getEvent()
            if not event:
                break
        stop()
        ```
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
        self.terminate()


    def getEvent(self) -> Union[str, None]:
        '''Read an event from the MQTT client (blocks until data is received)
            :returns str: an event from the MQTT client, or None if the client terminated
        '''
        try: 
            return self._subprocess.stdout.readline().strip()
        except IOError as e:
            # IOError if subprocess terminates while we're waiting for it to send output
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


    def _getMediaMatching(self, globPattern: str) -> List[str]:
        '''Search for media files matching globPattern under BASE_PATH
            :returns list[str]: list of paths of matching files, or None
        '''
        log.debug("searching for media files matching %s", globPattern)
        files: List[str] = glob.glob("%s/%s" % (config.get(self._CONFIG_SECTION, 'BASE_PATH'), globPattern))
        log.debug(f"found {len(files)} files: {files}")
        random.shuffle(files)
        return files


    def getMedia(self, precedence: List[str], params: Dict[str, str]) -> List[str]:
        '''Work out which media files to display on the marquee using precedence rules
            :params list[str] precedence: ordered list of search rules to try in turn
            :param dict[str,str] params: a dict of event parameters
            :returns str: path to a media file
        '''
        log.debug(f"precedence={precedence} params={params}")
        # get game filename without directory and extension (only last extension removed)
        gameBasename: str = os.path.splitext(os.path.basename(params.get('GamePath', '')))[0]
        log.debug(f"gameBasename={gameBasename}")
        
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
                    return [imagePath]
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
            files: List[str] = self._getMediaMatching(globPattern)
            if len(files) > 0:
                # if matching files were found, stop searching and return them
                return files
        # if no other suitable files, found return the default image
        return ['%s/default.png' % config.get(self._CONFIG_SECTION, 'BASE_PATH')]


    def show(self, filepaths: List[str], *args):
        '''Display a slideshow of images on the marquee.
            :param list[str] filepaths: list of paths to the media files to display
            :param Any args: any additional args to pass to the media player
        '''
        # terminate running media player if any
        self.terminate()
        # launch player to display media
        self._launch(
            [config.get(self._CONFIG_SECTION,'PLAYER')] + config.get(self._CONFIG_SECTION, 'PLAYER_OPTS').split() + filepaths + list(args)
        )


    def clear(self):
        '''Terminate media player process (if running) to clear marquee'''
        self.terminate()
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
        mediaPaths: List[str]  = self._mm.getMedia(precedence, params)
        # display media file if not already showing
        if mediaPaths is not []:
            self._mm.show(mediaPaths)



class Slideshow(object):

    _CONFIG_SECTION: ClassVar[str] = 'slideshow'
    "config file section for Slideshow"


    def __init__(self, imgPaths: List[str]) -> None:
        self._imgPaths = imgPaths
        self._imgTime: float = config.getfloat(self._CONFIG_SECTION, 'IMAGE_TIME', fallback=10.0)
        self._exitSignalled: Event = Event()
        signal.signal(signal.SIGTERM, self._sigHandler)


    def _runCmd(self, cmd: List[str], capture_output=True) -> bool:
        '''Run external command; capture output on failure
            :returns bool: True if command ran successfully, or False otherwise
        '''
        log.debug(f"run {cmd}")
        try:
            subprocess.run(
                cmd,
                capture_output=capture_output,
                check=True,
                text=True,
                timeout=1.0
            )
            return True
        except subprocess.CalledProcessError as cpe:
            log.error(f"failed to run {cmd}: {cpe}: exit code {cpe.returncode}\nstdout:{cpe.stdout}\nstderr:{cpe.stderr}")
            return False


    def showImage(self, imgPath: str):
        '''Display a single image on the framebuffer; exit leaving the image visible
        '''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'VIEWER')] + config.get(self._CONFIG_SECTION, 'VIEWER_OPTS').split() + [imgPath]
        self._runCmd(cmd)


    def clearImage(self):
        '''Clear the framebuffer'''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'CLEAR_CMD')] + config.get(self._CONFIG_SECTION, 'CLEAR_CMD_OPTS').split()
        self._runCmd(cmd)


    def run(self):
        '''Run slideshow in infinite loop until we received SIGTERM signal'''
        self._exitSignalled.clear()
        while not self._exitSignalled.is_set():
            for imgPath in self._imgPaths:
                self.showImage(imgPath)
                # wait for timeout to expire or be interrupteded by signal
                self._exitSignalled.wait(timeout=self._imgTime)
                self.clearImage()
                # log.debug(f'_exitSignalled={self._exitSignalled.is_set()}')
                if self._exitSignalled.is_set():
                    break
        # cleanup code here
        pass


    def _sigHandler(self, signum: int, _stackframe):
        log.info(f'received signal {signal.Signals(signum).name}')
        self._exitSignalled.set()




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
