#!/usr/bin/python3

'''dynquee - a dynamic marquee for Recalbox'''


import subprocess, signal, logging, logging.config, os, glob, random, threading
from configparser import ConfigParser
from threading import Thread, Event
import paho.mqtt.client as mqtt
from queue import SimpleQueue, Empty
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple, Optional

# Type aliases
EventParams = Dict[str, str]
SlideshowMediaSet = List[str]


# Module logging config file
_LOG_CONFIG_FILE: str = "dynquee.log.conf"

def getLogger() -> logging.Logger:
    '''Get module logger as defined by logging config file
        :return: a logging.Logger instance for this module
    '''
    logging.config.fileConfig(f"{os.path.dirname(__file__)}/{_LOG_CONFIG_FILE}")
    return logging.getLogger(__name__)


# Module config file
_CONFIG_FILE: str = "dynquee.ini"

def loadConfig() -> ConfigParser:
    '''Load config file in module directory into ConfigParser instance and return it'''
    config: ConfigParser = ConfigParser(empty_lines_in_values = False)
    _configFilesRead: List[str] = config.read(
        f"{os.path.dirname(__file__)}/{_CONFIG_FILE}",
    )
    logging.info(f"loaded config file(s): {_configFilesRead}")
    return config


class SignalHandler(object):
    '''Signals all registered Event objects if SIGTERM received to allow graceful exit'''

    def __init__(self):
        # trap SIGTERM signal to exit program gracefully
        signal.signal(signal.SIGTERM, self._sigReceived)
        self._events: List[Event] = []

    def addEvent(self, event: Event):
        '''Register event with signal handler'''
        self._events.append(event)

    def removeEvent(self, event: Event):
        '''Remove event registration'''
        self._events.remove(event)

    def _sigReceived(self, signum: int, _stackFrame):
        '''Called when SIGTERM received: set exit flags on registered Event objects'''
        log.info(f'received signal {signal.Signals(signum).name}')
        for event in self._events:
            event.set()

# Module signal handler instance
_signalHander: SignalHandler = SignalHandler()
"module signalHandler object"



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
        # event to signal exit of blocking getEvent() method
        self._exitEvent = Event()
        _signalHander.addEvent(self._exitEvent)
        # define callbacks
        self._client.on_connect = self._onConnect
        self._client.on_disconnect = self._onDisconnect
        self._client.on_message = self._onMessage


    def __del__(self):
        # disconnect from broker before exit
        self._client.disconnect()
        # de-register from signal handler
        _signalHander.removeEvent(self._exitEvent)


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


    def getEvent(self, checkInterval: float = 5.0) -> Optional[str]:
        '''Read an event from the message queue. Blocks until data is
            received or interrupted by an exit signal.
            :param checkInterval: how often to check if exit was requested (None = never check)
            :return: an event from the MQTT broker, or None if exit signal received while waiting
        '''
        while not self._exitEvent.is_set():
            try:
                return self._messageQueue.get(timeout = checkInterval).payload.decode("utf-8")
            except Empty:
                pass
        return None


    def getEventParams(self) -> Dict[str, str]:
        '''Read event params from ES state file, stripping any CR characters
            :return: a dict mapping param names to their values
        '''
        params: Dict[str,str] = {}
        with open(config.get(self._CONFIG_SECTION, 'es_state_file')) as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                log.debug(f"key={key} value={value}")
                params[key] = value
        return params



class MediaManager(object):
    '''Locates appropriate media files for an EmulationStation action using ordered search precendence rules.
        Rules are defined for each action in `[media]` section of config file: see config file for documentation.

        Call `getMedia()` to return a list of media files suitable for the action and selected system or game.
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
    "Glob patterns to find media files for each search term"


    @classmethod
    def isVideo(cls, filePath: str) -> bool:
        '''Test if specified file is a video file
            :return: True if file is a video file, False otherwise
        '''
        for ext in config.get(cls._CONFIG_SECTION, 'video_file_extensions').split():
            if filePath.endswith(ext):
                return True
        return False


    def _getMediaMatching(self, globPattern: str) -> SlideshowMediaSet:
        '''Search for media files matching globPattern within media directory
            :return: list of paths of matching files, or []
        '''
        log.debug(f"searching for media files matching {globPattern}")
        files: List[str] = glob.glob(
            f"{config.get(self._CONFIG_SECTION, 'media_path')}/{globPattern}"
        )
        log.debug(f"found {len(files)} files: {files}")
        return files


    def _getPrecedence(self, action: str) -> List[str]:
        '''Get precedence rules for this action from config file
            :return: precedence rule: an ordered list of search terms
        '''
        precedence: List[str] = config.get(
            self._CONFIG_SECTION,
            action,
            # if no rules defined for this action, use the default rules
            fallback = config.get(self._CONFIG_SECTION, 'default')
        ).split()
        log.debug(f"action={action}; search precedence={precedence}")
        return precedence


    def _getMediaForSearchTerm(self, searchTerm: str, evParams: EventParams) -> SlideshowMediaSet:
        '''Locate media matching a single component of a search rule. See config file
            for list of valid search terms.
            :param searchTerm: the search term
            :param evParams: a dict of event parameters
            :return: list of paths to media files, or [] if precedence rule == `blank`
        '''
        # if search term is `scraped` just return scraped image path (if set)
        if searchTerm == 'scraped':
            imagePath: str = evParams.get('ImagePath', '')
            log.debug(f"rule part=scraped ImagePath={imagePath}")
            if imagePath == '':
                return []
            else:
                return [imagePath]
        # skip unrecognised search terms
        if searchTerm not in self._GLOB_PATTERNS:
            log.warning(f"skipped unrecognised search term '{searchTerm}'")
            return []
        # get game filename without directory and extension (only last extension removed)
        gameBasename: str = os.path.splitext(os.path.basename(evParams.get('GamePath', '')))[0]
        log.debug(f"gameBasename={gameBasename}")
        # insert event params into search term's glob pattern
        globPattern: str = self._GLOB_PATTERNS[searchTerm].format(
            gameBasename = gameBasename,
            systemId = evParams.get('SystemId', '').lower(),
            publisher = evParams.get('Publisher', '').lower(),
            genre = evParams.get('Genre', '').lower(),
        )
        log.debug(f"searchTerm={searchTerm} globPattern={globPattern}")
        # return media files matching this glob pattern, if any
        return self._getMediaMatching(globPattern)


    def getMedia(self, evParams: EventParams) -> SlideshowMediaSet:
        '''Work out which media files to display for given action using search 
            precedence rules defined in config file.
            :param evParams: a dict of event parameters
            :return: list of paths to media files, or [] if marquee should be blank
        '''
        log.debug(f"params={evParams}")
        # get search precedence rule for this action
        action:str = evParams.get('Action', '')
        precedenceRule: List[str] = self._getPrecedence(action)
        # find best matching media file for system/game, trying each search term of precedence rule in turn
        for searchTerm in precedenceRule:
            # if `blank`, return empty list to indicate a blanked display
            if searchTerm == 'blank':
                return []
            # split complex terms e.g. `rom+scraped+publisher` into subterms
            # combine all found media into a single list
            files: List[str] = []
            for subTerm in searchTerm.split('+'):
                subTermFiles = self._getMediaForSearchTerm(subTerm, evParams)
                log.debug(f"subTerm={subTerm} subTermFiles={subTermFiles}")
                files += subTermFiles
            # if matching files were found for this term, return them
            if files:
                return files
        # if no matching files were found for any search term, return the default image as a last resort
        else:
            return [f"{config.get(self._CONFIG_SECTION, 'media_path')}/{config.get(self._CONFIG_SECTION, 'default_image')}"]


    def getStartupMedia(self) -> SlideshowMediaSet:
        '''Get list of media files to be played at program startup'''
        log.debug(f"getting startup media files")
        globPattern: str = self._GLOB_PATTERNS['startup']
        return self._getMediaMatching(globPattern)


class Slideshow(object):
    '''Displays slideshow of images/videos on the marquee.
        Uses 2 threads:
        1. _queueReaderThread: watches queue for new media, dispatches slideshow thread
        2. _slideshowThread: runs slideshow in continuous loop; waits for a media change event before exiting

        Call `setMedia()` to change the media set displayed.

        Call  `stop()` to stop queue reader thread cleanly before exit.
    '''

    _CONFIG_SECTION: ClassVar[str] = 'slideshow'
    "config file section for Slideshow"


    def __init__(self):
        self._imgDisplayTime: float = config.getfloat(self._CONFIG_SECTION, 'image_display_time', fallback=10)
        "how long to display each image in a slideshow (seconds)"
        self._maxVideoTime: float = config.getfloat(self._CONFIG_SECTION, 'max_video_time', fallback=120)
        "maximum time to let video file play before being stopped (seconds)"

        # properties for communication between threads
        self._queue: SimpleQueue[SlideshowMediaSet] = SimpleQueue()
        "queue of slideshow media sets"
        self._currentMedia: SlideshowMediaSet = []
        "the media set currently displayed"
        self._mediaChange: Event = Event()
        "event to indicate slideshow media is to be changed"

        # threads & subprocesses
        self._slideshowThread: Optional[Thread] = None
        "slideshow worker thread"
        self._queueReaderThread: Thread = Thread(
            name = 'queue_reader_thread',
            target = self._readMediaQueue,
            daemon = True
        )
        "media queue reader thread"
        self._subProcess: Optional[subprocess.Popen] = None
        "media player/viewer subprocess"
        
        # handle program exit cleanly
        self._exitSignalled: Event = Event()
        "event to indicate program exit has been signalled"
        # register with signal handler to exit cleanly if SIGTERM received
        _signalHander.addEvent(self._exitSignalled)

        # set initial framebuffer resolution if set in config files
        self._setFramebufferResolution()
        # start queue reader thread
        self._queueReaderThread.start()


    def __del__(self):
        self.stop()
        # de-register from signal handler
        _signalHander.removeEvent(self._exitSignalled)


    def _setFramebufferResolution(self):
        '''Force a specific framebuffer resolution if defined in config file'''
        fbResCmd: str = config.get(
            self._CONFIG_SECTION, 'framebuffer_resolution_cmd',
            fallback=''
        ).split()
        if fbResCmd:
            self._runCmd(fbResCmd, waitForExit=True, timeout=self._timeout)


    def _runCmd(self, cmd: List[str]) -> bool:
        '''Launch external command
            :param cmd: sequence of program arguments passed to Popen constructor
            :return: True if command launched successfully, or False otherwise
        '''
        log.debug(f"cmd={cmd}")
        try:
            self._subProcess = subprocess.Popen(cmd)
            return True
        except OSError as e:
            log.error(f"failed to run {cmd}: {e}")
            return False


    def _showImage(self, imgPath: str):
        '''Run the display image command defined in config file
            :param imgPath: full path to image file
        '''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'viewer')] + config.get(self._CONFIG_SECTION, 'viewer_opts').split() + [imgPath]
        self._runCmd(cmd)


    def _clearImage(self):
        '''Run the clear image command defined in config file (if any)'''
        clearCmd: str = config.get(self._CONFIG_SECTION,'clear_cmd')
        if clearCmd:
            cmd: List[str] = [clearCmd] + config.get(self._CONFIG_SECTION, 'clear_cmd_opts').split()
            self._runCmd(cmd)


    def _startVideo(self, videoPath: str):
        '''Launch video player command defined in config file.
            To stop video, call `_stopVideo()` to terminate video player process.
            :param videoPath: full path to video file
        '''
        cmd: List[str] = [config.get(self._CONFIG_SECTION,'video_player')] + config.get(self._CONFIG_SECTION, 'video_player_opts').split() + [videoPath]
        self._runCmd(cmd)


    def _stopVideo(self, timeout: float = 3.0):
        '''Stop running video player (if running) by terminating process
            :param timeout: how long to wait for subprocess to exit
        '''
        if self._subProcess is not None:
            # try to terminate subprocess cleanly
            self._subProcess.terminate()
            try:
                rc: int = self._subProcess.wait(timeout)
                log.debug(f"terminated video player: rc={rc}")
            except subprocess.TimeoutExpired:
                #subprocess did not exit within timeout so kill it
                self._subProcess.kill()
                log.debug(f"killed (SIGKILL) video player subprocess pid={self._subProcess.pid}")


    def _runSlideshow(self):
        '''Slideshow thread: loop a slideshow media set until a `_mediaChange` event occurs.
            Gets media set to show from `_currentMedia` property
        '''
        mediaPaths: SlideshowMediaSet = self._currentMedia
        log.debug(f"slideshow worker thread start")
        while not self._mediaChange.is_set():
            # random order of media each time through slideshow
            random.shuffle(mediaPaths)
            for mediaFile in mediaPaths:
                # is file still image or video?
                if MediaManager.isVideo(mediaFile):
                    # start video, wait for clip to finish or `_maxVideoTime` to expire
                    #  or _mediaChange event to occur, then stop it
                    self._startVideo(mediaFile)
                    log.debug(f"showing video for up to {self._maxVideoTime}s")
                    self._mediaChange.wait(timeout = self._maxVideoTime)
                    self._stopVideo()
                else:
                    # show image, wait for `_imgDisplayTime` to expire or _mediaChange event, then clear it
                    self._showImage(mediaFile)
                    # If we only have one image, just display it and wait until _mediaChange signalled
                    # Note: this only works if viewer leaves image up on framebuffer like fbv?
                    if len(mediaPaths) == 1 and not MediaManager.isVideo(mediaPaths[0]):
                        log.debug("single image file in slideshow: waiting for _mediaChange event")
                        self._mediaChange.wait()
                    else:
                        # leave image showing for configured time
                        self._mediaChange.wait(timeout = self._imgDisplayTime)
                        log.debug(f"showing image for up to {self._imgDisplayTime}s")
                    self._clearImage()
                # exit slideshow if _mediaChangeRequested flag set
                if self._mediaChange.is_set():
                    log.debug(f"_mediaChangeRequested={self._mediaChange.is_set()}")
                    break
                # pause between slideshow images/clips
                self._mediaChange.wait(timeout = config.getfloat(self._CONFIG_SECTION, 'time_between_slides'))
        # slideshow loop interrupted by _mediaChange event
        log.debug(f"slideshow worker thread exit")


    def _readMediaQueue(self):
        '''Media queue reader thread: read media sets from the media queue
            and launch slideshow thread to display them.
            Exit on `_exitSignalled` event.

            Sends `_mediaChangeRequested` event when a new media set is queued.
        '''
        log.debug(f"media queue thread start")
        while not self._exitSignalled.is_set():
            log.debug("wait for slideshow media set")
            mediaPaths: SlideshowMediaSet = self._queue.get(block = True)
# TODO: if qsize > 1, jump to end of queue? But may cause a deadlock?

            # Check for exit signal before launching a slideshow:
            # this allows stop() to enqueue a dummy media set to cause exit
            if self._exitSignalled.is_set():
                break
            # only change slideshow if new media set is different
            mediaChanged: bool = not (mediaPaths == self._currentMedia)
            log.debug(f"media changed={mediaChanged} mediaPaths={mediaPaths} _currentMedia={self._currentMedia}")
            if mediaChanged:
                # indicate a media change and wait for current slideshow (if any) to exit
                log.info(f"slideshow media changed: {mediaPaths}")
                self._mediaChange.set()
                if self._slideshowThread is not None:
                    self._slideshowThread.join()
                # record current media set
                self._mediaChange.clear()
                # start new slideshow unless blanked display requested
                self._currentMedia = mediaPaths.copy()
                if mediaPaths:
                    self._slideshowThread = Thread(
                        name = 'slideshow_thread',
                        target = self._runSlideshow,
                    )
                    self._slideshowThread.start()
                else:
                    # Note: should only happen if 'blank' specified in search precedence rule;
                    # MediaManager.getMedia() always returns default image as last resort
                    log.info("'blank' specified in search precedence rule: blanking display")
        # queue reader loop interrupted by stop() or _exitSignalled event
        log.debug(f"media queue thread exit")


    def setMedia(self, mediaPaths: SlideshowMediaSet):
        '''Queue a media set for display.
            :param mediaPaths: list of media files to be displayed as a slideshow.
              Duplicates are removed before queueing.
        '''
        # Normalise media set: remove duplicates and sort
        # (allows queue reader to check if media set has changed)
        mediaPaths = list(set(mediaPaths))
        mediaPaths.sort()
        self._queue.put(mediaPaths)


    def stop(self):
        '''Stop the slideshow and clear the display; also stops queue reader thread.
        '''
        log.debug("slideshow stop requested")
        # signal any running slideshow thread to exit and wait
        self._mediaChange.set()
        if self._slideshowThread is not None and self._slideshowThread.is_alive():
            log.debug(f"waiting for slideshow thread to exit: {self._slideshowThread}")
            self._slideshowThread.join()
        # signal queue reader thread to exit and wait
        # enqueue a dummy slideshow to force a check of _exitSignalled event status
        self._exitSignalled.set()
        self.setMedia([])
        log.debug(f"waiting for queue reader thread to exit: {self._queueReaderThread}")
        self._queueReaderThread.join()
        log.debug(f"remaining threads: {threading.enumerate()}")



class EventHandler(object):
    '''Receives events from MQTTSubscriber, uses MediaManager to find images and Slideshow to show them'''

    _CONFIG_SECTION: ClassVar[str] = 'media'
    "config file section for EventHandler"


    @dataclass(frozen = True)
    class ESState(object):
        '''Keeps track of state of Emulation Station (immutable)'''
        action: str = ''
        system: str = ''
        game: str = ''
        isFolder: bool = False

        @classmethod
        def fromEvent(cls, evParams: EventParams) -> 'EventHandler.ESState':
            '''Create ESState object from supplied event parameters'''
            return EventHandler.ESState(
                action = evParams.get('Action', ''),
                system = evParams.get('SystemId', ''),
                game = evParams.get('GamePath', ''),
                isFolder = (evParams.get('IsFolder') == '1')
            )


    def __init__(self):
        self._mqttSubscriber: MQTTSubscriber = MQTTSubscriber()
        self._mediaManager: MediaManager = MediaManager()
        self._slideshow: Slideshow = Slideshow()
        self._mqttSubscriber.start()
        self._slideshow.start()
        # initialise record of EmulationStation state
        self._currentState: EventHandler.ESState = EventHandler.ESState()
        self._previousEvParams: EventParams = {}
        # in case first event is 'sleep', initialise state before sleep
        self._stateBeforeSleep = self._currentState


    def readEvents(self):
        '''Read and handle all events from the MQTTSubscriber'''
        while True:
            event: str = self._mqttSubscriber.getEvent()
            # exit loop if interrupted by TERM signal
            if not event:
                self._slideshow.stop()
                break
            log.debug(f'event received: {event}')
            params: EventParams = self._mqttSubscriber.getEventParams()
            self._handleEvent(params)


    def _handleEvent(self, evParams: EventParams):
        '''Find appropriate media files for the event and display them
            :param evParams: a dict of event parameters
        '''
        log.info(f"event params={evParams}")
        changeOn: str
        noChangeOn: str
        (changeOn, noChangeOn) = self._getStateChangeRules()       
        # has EmulationStation state changed?
        stateChanged: bool = self._hasStateChanged(evParams, changeOn, noChangeOn)
        # update state: on wakeup, restore state & evParams from before sleep
        evParams = self._updateState(evParams)
        if stateChanged:
            log.info(f"EmulationStation state changed: _currentState={self._currentState}")
            # search for media files
            mediaPaths: SlideshowMediaSet = self._mediaManager.getMedia(evParams)
            log.debug(f'queue slideshow media={mediaPaths}')
            self._slideshow.setMedia(mediaPaths)


    def startup(self):
        '''Show slideshow of startup files'''
        mediaPaths: SlideshowMediaSet = self._mediaManager.getStartupMedia()
        log.info(f"startup slideshow media={mediaPaths}")
        if mediaPaths:
            self._slideshow.setMedia(mediaPaths)


    def _updateState(self, evParams: EventParams) -> EventParams:
        '''Update record of EmulationStation state with provided values
            :param evParams: event params
            :return: either same event params as passed in, or event params before sleep if action is `wakeup`
        '''
        # workaround for ES bug: ES doesn't consistently fire another event after wakeup
        # if action == sleep, record state before sleep so we can restore it after wakeup
        action: str = evParams.get('Action', '')
        if action == 'sleep':
            self._stateBeforeSleep = self._currentState
            log.info(f"record _stateBeforeSleep={self._stateBeforeSleep}")
        # update record of evParams unless action is sleep or wakeup
        if action not in ['sleep', 'wakeup']:
            self._previousEvParams = evParams.copy()
        # update state
        self._currentState = self.ESState.fromEvent(evParams)
        # if action is wakeup, restore state and evParams before sleep (ES bug workaround)
        if action == 'wakeup':
            self._currentState = self._stateBeforeSleep
            evParams = self._previousEvParams
            log.info(f"restore _stateBeforeSleep={self._stateBeforeSleep}")
            log.info(f"restore _evParams={evParams}")
        log.debug(f"_currentState={self._currentState}")
        return evParams


    def _getStateChangeRules(self) -> Tuple[str, str]:
        '''Look up state change rules in config file
            :return: tuple of values in the format (change_on, no_change_on)
        '''
        # get state change rules from config file
        noChangeOn: str = config.get(self._CONFIG_SECTION, 'no_change_on')
        changeOn: str = config.get(self._CONFIG_SECTION, 'change_on')
        return (changeOn, noChangeOn)
        

    def _hasStateChanged(self, evParams: EventParams, changeOn: str, noChangeOn:str) -> bool:
            '''Determine if EmulationStation's state has changed enough to change displayed media.
                Follows rules defined in config file.
                :param evParams: dict of EmulationStation event params
                :param changeOn: rule specifying when to change state
                :param noChangeOn: rule specifying which actions do not change state
                :return: True if state has changed
            '''
            newState: EventHandler.ESState = EventHandler.ESState.fromEvent(evParams)
            log.debug(f"changeOn={changeOn} noChangeOn={noChangeOn}")
            log.debug(f"_currentState={self._currentState} newState={newState}")

            # 'wakeup' action always causes a state change as we restore the state before sleep
            if newState.action == 'wakeup':
                return True
            # Use rules defined in config file to determine if state has changed
            # no change if action is ignored or `never` change specified
            if (newState.action and (newState.action in noChangeOn)) or (changeOn == 'never'):
                return False           
            # is `always` change specified?
            elif changeOn == 'always':
                return True
            # has action changed from previous action?
            elif changeOn == 'action':
                return not newState.action == self._currentState.action
            # has system changed?
            elif changeOn == 'system':
                return not newState.system == self._currentState.system
            # has game changed?
            elif changeOn == 'game':
                return not newState.game == self._currentState.game
            # has system OR game changed?
            elif changeOn == 'system/game':
                log.debug('if changeOn=system/game')
                return not ((newState.system == self._currentState.system) and (newState.game == self._currentState.game))
            else:
                # unrecognised action in state change rule: log it
                log.error((
                    "Unrecognised state change rule - check config file: "
                    f" changeOn='{changeOn}' noChangeOn='{noChangeOn}'"
                    f" _currentState={self._currentState} newState={newState}"
                ))
                # change marquee
                return True



# Configure logging from log config file
log: logging.Logger = getLogger()

# Uncomment for debug output:
#log.setLevel(logging.DEBUG)

# Read config file
config: ConfigParser = loadConfig()


### main ###

if __name__ == '__main__':
    try:
        log.info("dynquee start")
        eventHandler: EventHandler = EventHandler()
        eventHandler.startup()
        eventHandler.readEvents()
        log.info('dynquee exit')
    except Exception as e:
        # log any uncaught exception before exit
        log.critical(f"uncaught exception: {e}", exc_info=True)
