#!/usr/bin/python3

import subprocess, signal, logging, os, glob, random, time
from configparser import ConfigParser
from threading import Thread, Event
import paho.mqtt.client as mqtt
from queue import SimpleQueue
from typing import ClassVar, Dict, List, Optional

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
        Directory search order:
        1. /boot
        2. module directory
        3. current directory
    '''
    config: ConfigParser = ConfigParser(empty_lines_in_values = False)
    _configFilesRead: List[str] = config.read([
        f"/boot/{_CONFIG_FILE}",
        f"{os.path.dirname(__file__)}/{_CONFIG_FILE}",
        _CONFIG_FILE
    ])
    log.info(f"loaded config file(s): {_configFilesRead}")
    return config



class MQTTSubscriber(object):
    '''MQTT subscriber: handles connection to broker to receive events from 
        EmulationStation and read event params from event file.

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


    def __init__(self):
        self._client = mqtt.Client()
        # log mqtt.Client messages to module logger
        self._client.enable_logger(logger = log)
        # queue to store incoming messages (thread safe)
        self._messageQueue: SimpleQueue = SimpleQueue()
        # define callbacks
        self._client.on_connect = self._onConnect
        self._client.on_disconnect = self._onDisconnect
        self._client.on_message = self._onMessage


    def __del__(self):
        # disconnect from broker before exit
        self._client.disconnect()


    def start(self, *args):
        '''Connect to the MQTT broker'''
        host: str = config.get(self._CONFIG_SECTION, 'host')
        port: int = config.getint(self._CONFIG_SECTION, 'port')
        keepalive: int = config.getint(self._CONFIG_SECTION, 'keepalive', fallback=60)
        log.info(f"connecting to MQTT broker host={host} port={port} keepalive={keepalive}")
        self._client.connect(
            host = host,
            port = port,
            keepalive = keepalive,
            *args
        )
        self._client.loop_start()

    
    def stop(self):
        self._client.disconnect()

    
    def _onConnect(self, client, user, flags, rc: int):
        topic: str = config.get(self._CONFIG_SECTION, 'topic')
        self._client.subscribe(topic)
        log.info(f"connected to MQTT broker rc={rc} topic={topic}")


    def _onDisconnect(self, client, userdata, rc: int):
        log.info(f"disconnected from MQTT broker rc={rc}")
        self._client.loop_stop()


    def _onMessage(self, client, userdata, message: mqtt.MQTTMessage):
        '''Add incoming message to message queue'''
        log.debug(f"message topic={message.topic} payload={message.payload}")
        self._messageQueue.put(message)


    def getEvent(self) -> str:
        '''Read an event from the message queue (blocks until data is received)
            :returns str: an event from the MQTT broker
        '''
        return self._messageQueue.get().payload.decode("utf-8")


    def getEventParams(self) -> Dict[str, str]:
        '''Read event params from ES state file, stripping any CR characters
            :returns dict: a dict mapping param names to their values
        '''
        params: Dict[str,str] = {}
        with open(config.get(self._CONFIG_SECTION, 'es_state_file')) as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                log.debug(f"key={key} value={value}")
                params[key] = value
        return params



class MediaManager(object):
    '''Finds appropriate media files for an EmulationStation action using ordered search precendence rules.
        Rules are defined for each action in [media] section of config file. Valid search rules can contain:
        * `rom`: ROM-specific media e.g. marquee image for the selected game
        * `scraped`: the selected game's scraped image
        * `publisher`: media relating to the publisher of game e.g. Atari or Taito logo
        * `genre`: media relating to genre of game e.g. shooters, platform games
        * `system`: media relating to game system e.g. ZX Spectrum or SNES logo
        * `generic`: generic media unrelated to a game, system or publisher

        Call `getMedia()` to return a list of media files suitable for the selected system or game.
    '''

    _CONFIG_SECTION: ClassVar[str] = 'media'
    "config file section for MediaManager"


    _GLOB_PATTERNS: ClassVar[Dict[str, str]] = {
        'rom': "{systemId}/{gameBasename}.*",
        'publisher': "publisher/{publisher}.*",
        'genre': "genre/{genre}.*",
        'system': "system/{systemId}.*",
        'generic': "generic/*",
        'startup': "startup/*" # files to show on startup
    }
    "Glob patterns to find media files for each search rule component"


    @classmethod
    def isVideo(cls, filePath: str) -> bool:
        '''Test if specified file is a video file
            :returns: True is file is a video file, False otherwise
        '''
        if filePath.endswith('.mp4'):
            return True
        return False
        # TODO: implement properly


    def _getMediaMatching(self, globPattern: str) -> List[str]:
        '''Search for media files matching globPattern within BASE_PATH
            :returns list[str]: list of paths of matching files, or []
        '''
        log.debug(f"searching for media files matching {globPattern}")
        files: List[str] = glob.glob(
            f"{config.get(self._CONFIG_SECTION, 'base_path')}/{globPattern}"
        )
        log.debug(f"found {len(files)} files: {files}")
        return files


    def _getPrecedence(self, action: str) -> List[str]:
        '''Get precedence rules for this action from config file
            :returns list[str]: ordered list of precedence rules
        '''
        precedence: List[str] = config.get(
            self._CONFIG_SECTION,
            action,
            # if no rules defined for this action, use the default rules
            fallback = config.get(self._CONFIG_SECTION, 'default')
        ).split()
        log.info(f"action={action}; search precedence={precedence}")
        return precedence


    def getMedia(self, action: str, params: Dict[str, str]) -> List[str]:
        '''Work out which media files to display using precedence rules
            :params str action: EmulationStation action
            :param dict[str,str] params: a dict of event parameters
            :returns list[str]: paths to media files, or [] if precedence rule is `blank`
        '''
        log.debug(f"action={action} params={params}")
        # get game filename without directory and extension (only last extension removed)
        gameBasename: str = os.path.splitext(os.path.basename(params.get('GamePath', '')))[0]
        log.debug(f"gameBasename={gameBasename}")
        # get search precedence rule for this action
        precedence: List[str] = self._getPrecedence(action)

        # find best matching media file for system/game, trying each component of precedence rule in turn
        for ruleItem in precedence:
            # if blank, return empty list to indicate a blanked display
            if ruleItem == 'blank':
                return []
            # if using scraped image just return its path
            if ruleItem == 'scraped':
                imagePath: str = params.get('ImagePath', '')
                log.debug(f"rule=scraped ImagePath={imagePath}")
                if imagePath == '':
                    # skip rule if no scraped image exists
                    continue
                else:
                    return [imagePath]
            # skip unrecognised rules
            if ruleItem not in self._GLOB_PATTERNS:
                log.warning(f"skipped unrecognised rule name '{ruleItem}'")
                continue
            # insert event params into rule's glob pattern
            globPattern: str = self._GLOB_PATTERNS[ruleItem].format(
                gameBasename = gameBasename,
                systemId = params.get('SystemId', '').lower(),
                publisher = params.get('Publisher', '').lower(),
                genre = params.get('Genre', '').lower(),
            )
            log.debug(f"rule={ruleItem} globPattern={globPattern}")
            # find media files matching this glob pattern
            files: List[str] = self._getMediaMatching(globPattern)
            if files:
                # if matching files were found, stop searching & return them
                return files
        # if no other suitable files found, return a list containing just the default image
        return [f"{config.get(self._CONFIG_SECTION, 'base_path')}/{config.get(self._CONFIG_SECTION, 'default_image')}"]


    def getStartupMedia(self) -> List[str]:
        '''Get list of media files to be played at program startup'''
        log.debug(f"getting startup media files")
        globPattern: str = self._GLOB_PATTERNS['startup']
        return self._getMediaMatching(globPattern)



class Slideshow(object):
    '''Display slideshow of images on the marquee; runs in a separate thread.
        Use `run()` to start slideshow, `stop()` to stop
    '''

    _CONFIG_SECTION: ClassVar[str] = 'slideshow'
    "config file section for Slideshow"


    def __init__(self, timeout: float = 3.0):
        self._imgDisplayTime: float = config.getfloat(self._CONFIG_SECTION, 'image_display_time', fallback=10)
        "how long to display each image in a slideshow (seconds)"
        self._maxVideoTime: float = config.getfloat(self._CONFIG_SECTION, 'max_video_time', fallback=120)
        "maximum time to let video file play before being stopped (seconds)"
        self._timeout = timeout
        "how long to wait for external processes to complete (seconds)"
        self._exitSignalled: Event = Event()
        "indicates whether slideshow exit was requested"
        self._workerThread: Optional[Thread] = None
        "slideshow worker thread"
        self._subProcess: Optional[subprocess.Popen] = None
        "media player/viewer subprocess"
        
        # trap SIGTERM signal to exit slideshow gracefully
        signal.signal(signal.SIGTERM, self._sigHandler)

    
    def _runCmd(self, cmd: List[str], waitForExit: bool = False, timeout: float = 0) -> bool:
        '''Run external command
            :params waitForExit: if True waits for command to complete, otherwise returns immediately
            :params timeout: how long to wait for command to complete (seconds)
            :returns bool: True if command launched successfully, or False otherwise
        '''
        log.debug(f"cmd={cmd}")
        try:
            self._subProcess = subprocess.Popen(cmd)
            if waitForExit:
                # wait at most `timeout` seconds for subprocess to complete
                try:
                    log.debug(f"waiting up to {timeout}s for process to complete")
                    self._subProcess.wait(timeout)
                    log.debug(f"process completed within {timeout}s timeout")
                except subprocess.TimeoutExpired:
                    log.info(f"process did not complete within {timeout}s timeout")
            return True
        except OSError as e:
            log.error(f"failed to run {cmd}: {e}")
            return False


    def showImage(self, imgPath: str):
        '''Run the display image command defined in config file
            :param str imgPath: full path to image
        '''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'viewer')] + config.get(self._CONFIG_SECTION, 'viewer_opts').split() + [imgPath]
        self._runCmd(cmd)


    def clearImage(self):
        '''Run the clear image command defined in config file (if any)'''
        clearCmd: str = config.get(self._CONFIG_SECTION,'clear_cmd')
        if clearCmd:
            cmd: List[str] = [clearCmd] + config.get(self._CONFIG_SECTION, 'clear_cmd_opts').split()
            self._runCmd(cmd)


    def showVideo(self, videoPath: str, maxVideoTime: float):
        '''Launch video player command defined in config file: should play video to end then exit.
            To stop video, call `stopVideo()` to terminate process.
            :param str videoPath: full path to video file
        '''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'video_player')] + config.get(self._CONFIG_SECTION, 'video_player_opts').split() + [videoPath]
        self._runCmd(cmd, waitForExit=True, timeout=maxVideoTime)


    def stopVideo(self):
        '''Stop running video player (if running) by terminating process'''
        if self._subProcess is not None:
            self._subProcess.terminate()
            try:
                rc: int = self._subProcess.wait(timeout = self._timeout)
            except subprocess.TimeoutExpired:
                pass
            log.debug(f"terminated video player: rc={rc}")


    def _doRun(self, mediaPaths: List[str]):
        '''Thread worker: loop image/video slideshow for ever until `stop()` called or SIGTERM signal received
            :params mediaPaths: list of full paths to media files to show
        '''
        self._exitSignalled.clear()
        while not self._exitSignalled.is_set():
            # random order of media each time through slideshow
            random.shuffle(mediaPaths)
            for mediaFile in mediaPaths:
                # is file still image or video?
                isVideo: bool = MediaManager.isVideo(mediaFile)
                if isVideo:
                    # start video, wait for clip to finish or `_maxVideoTime` to expire, and stop it
                    self.showVideo(mediaFile, self._maxVideoTime)
                    self.stopVideo()
                else:
                    # show image, wait for `_imgDisplayTime` to expire or SIGTERM, and clear it
                    self.showImage(mediaFile)
                    # if we only have 1 image, just display it and exit
                    # Note: this only works if viewer leaves image up on framebuffer like fbv
                    if len(mediaPaths) == 1:
                        break
                    self._exitSignalled.wait(timeout = self._imgDisplayTime)
                    self.clearImage()
                # exit slideshow if SIGTERM received or `stop()` was called
                if self._exitSignalled.is_set():
                    break
        # clear reference to slideshow worker thread once finished
        self._workerThread = None
    

    def run(self, imgPaths: List[str]):
        '''Start thread to run randomised slideshow of images until `stop()` called or we receive SIGTERM signal
            :param list[str] imgPaths: list of paths to images
        '''
        self._workerThread = Thread(
            name = 'slideshow_thread',
            target = self._doRun,
            args = (imgPaths,),
            daemon = True # terminate slideshow thread on exit
        )
        self._workerThread.start()


    def stop(self):
        '''Stop the slideshow'''
        log.debug("Slideshow stop requested")
        self._exitSignalled.set()
        self.stopVideo()
        self.clearImage()


    def _sigHandler(self, signum: int, _stackframe):
        '''Called when SIGTERM or SIGCHLD received'''
        log.info(f'received signal {signal.Signals(signum).name}')
        self._exitSignalled.set()




class EventHandler(object):
    '''Receives events from MQTTSubscriber, uses MediaManager to find images and Slideshow to show them'''

    _CONFIG_SECTION: ClassVar[str] = 'search'
    "config file section for EventHandler"

    
    def __init__(self):
        self._ms: MQTTSubscriber = MQTTSubscriber()
        self._mm: MediaManager = MediaManager()
        self._sl: Slideshow = Slideshow()
        self._ms.start()
        # initialise record of EmulationStation state
        self._currentAction = None
        self._currentSystem = None
        self._currentGame = None


    def readEvents(self):
        '''Read and handle all events from the MQTTSubscriber'''
        while True:
            event: str = self._ms.getEvent()
            

            # TODO: handle ES exit cleanly
            # doesn't exit nicely when SIGTERM
            # global signal handler for module? module level Event()?

            if not event or event == 'quit':
                break
            log.debug(f'event received: {event}')
            params: Dict[str, str] = self._ms.getEventParams()
            self._handleEvent(params.get('Action'), params)


    def _handleEvent(self, action: str, evParams: Dict[str, str]):
        '''Find appropriate media files for the event and display them
            :param str event: EmulationStation action 
            :param dict[str,str] params: a dict of event parameters
        '''
        log.debug(f"action={action}, params={evParams}")
        # has ES state changed: do we need to change displayed media?
        stateChanged: bool = self._hasStateChanged(action, evParams)
        self._updateState(action, evParams)
        if not stateChanged:
            # do nothing if ES state has not changed
            return
        log.info(f"EmulationStation state changed: action={action} system={self._currentSystem} game={self._currentGame}")
        # search for media files
        mediaPaths: List[str] = self._mm.getMedia(action, evParams)
        # if no files returned, blank display
        # Note: should only happen if 'blank' found in predence rule; MediaManager.getMedia() always returns default image as last resort
        if not mediaPaths:
            self._sl.stop()
            log.info("'blank' specified in search precedence rule: clearing display")
        else:
            # display media slideshow
            log.info(f'new slideshow media={mediaPaths}')
            # stop existing slideshow if running
            self._sl.stop()
            time.sleep(0.2)
            # start new slideshow
            self._sl.run(mediaPaths)


    def startup(self):
        '''Show slideshow of startup files'''
        mediaPaths: List[str] = self._mm.getStartupMedia()
        log.info(f"startup slideshow media={mediaPaths}")
        if mediaPaths:
            self._sl.run(mediaPaths)


    def _updateState(self, action: str, evParams: Dict[str, str]):
        '''Update record of EmulationStation state with provided values'''
        self._currentAction = action
        self._currentSystem = evParams.get('SystemId')
        self._currentGame = evParams.get('GamePath')
        log.debug(f"_currentAction={self._currentAction} _currentSystem={self._currentSystem} _currentGame={self._currentGame}")


    def _hasStateChanged(self, newAction: str, evParams: Dict[str, str]) -> bool:
            '''Determine if EmulationStation's state has changed enough for us to change displayed media
                :returns bool: True if state has changed
            '''
            newSystem: str = evParams.get('SystemId', '')
            newGame: str = evParams.get('GamePath', '')
            log.debug(f"_currentAction={self._currentAction} newAction={newAction}")
            log.debug(f"currentSystem={self._currentSystem} newSystem={newSystem}")
            log.debug(f"_currentGame={self._currentGame} newGame={newGame}")
            # starting a game always causes a state change
            # note: ignore endgame action as it's followed quickly by gamelistbrowsing event
            if newAction == 'rungame':
                return True
            # same action & same system = no state change
            if newAction == self._currentAction and newSystem == self._currentSystem:
                return False
            # otherwise state has changed
            return True




# Logging setup
# TODO: Should eventually log to /recalbox/share/system/logs/ ?
# for now, just log to stderr
log: logging.Logger = getLogger(logging.INFO)

# Uncomment for debug output:
#log.setLevel(logging.DEBUG)


# Read config file
config: ConfigParser = loadConfig()


### main ###

if __name__ == '__main__':
    eh: EventHandler = EventHandler()
    eh.startup()
    eh.readEvents()
    log.debug('exiting')
