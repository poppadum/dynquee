#!/usr/bin/python3

# integration tests for dynquee.EventHandler class
# uses unittest framework

import unittest, logging, time, io, os
from dynquee import EventHandler, MQTTSubscriber, MediaManager, Slideshow, log, config
from threading import Thread
from typing import Optional, Dict, List

log.setLevel(logging.INFO)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_dynquee.ini" % os.path.dirname(__file__)
    config.read(configFile)
    log.info("loaded test config file: %s" % configFile)


class MockMQTTSubscriber(MQTTSubscriber):
    '''Mocked MockMQTTSubscriber: can be told what actions to fire'''
    # _VALID_ACTIONS = ['systembrowsing','gamelistbrowsing','rungame','endgame']
    def __init__(self):
        self._disconnect = False
        self._nextEvent = {}
        self._nextEventProcessed = True
    
    def __del__(self):
        pass
    def start(self):
        pass
    def _onConnect(self, client, user, flags, rc: int):
        pass
    
    def _onDisconnect(self, client, user, flags, rc: int):
        pass

    def stop(self):
        self._disconnect = True

    def getEvent(self, checkInterval: float = 5.0) -> Optional[str]:
        # wait until we have an event or disconnect
        while True:
            if self._disconnect: break
            if not self._nextEventProcessed: break
            time.sleep(0.1)
        if self._disconnect: return None
        action:str = self._nextEvent.get('action')
        log.info(f"generate action {action}")
        # mark event processed
        self._nextEventProcessed = True
        return action
    
    def getEventParams(self) -> Dict[str, str]:
        evParams = self._nextEvent.get('evParams')
        evParams['Action'] = self._nextEvent.get('action')
        log.info(f"generate evParams {evParams}")
        return evParams
    
    def mockEvent(self, action: str, evParams: Dict[str, str]):
        self._nextEvent = {
            'action': action,
            'evParams': evParams
        }
        self._nextEventProcessed = False


class MockSlideshow(Slideshow):
    '''Mock Slideshow: does not launch any subprocess'''
    def _runCmd(self, cmd: List[str], waitForExit: bool = False, timeout: float = 0) -> bool:
        pass
    def run(self, mediaPaths: List[str]):
        pass


class MockEventHandler(EventHandler):
    '''Mock EventHandler: uses MockMQTTSubcriber & MockSlideshow'''
    
    def __init__(self):
        self._mqttSubscriber: MQTTSubscriber = MockMQTTSubscriber()
        self._mediaManager: MediaManager = MediaManager()
        self._slideshow: Slideshow = MockSlideshow()
        # initialise record of EmulationStation state
        self._currentState = self.ESState()


class testEventHandler(unittest.TestCase):

    def setUp(self):
        '''create a MockEventHandler and start the event send thread'''
        self.eh = MockEventHandler()
        self.eh._mqttSubscriber: MockMQTTSubscriber = MockMQTTSubscriber()
        evTh = Thread(
            name = 'read_event_thread',
            target = self.eh.readEvents,
            daemon = True
        )
        evTh.start()
        self.wait()

    def wait(self):
        '''time delay to let event propagate'''
        time.sleep(1.0)

    def testEventHandlerSystem(self):
        evParams = {
            'SystemId': 'snes',
            'GamePath': '/path/to/mario.zip',
            'IsFolder': '0'
        }

        with self.assertLogs(log, logging.INFO) as cm:
            self.eh._mqttSubscriber.mockEvent('systembrowsing', {})
            self.wait()
            self.assertEqual(cm.output[0], 'INFO:dynquee:generate action systembrowsing')
            self.assertEqual(cm.output[2], "INFO:dynquee:action=systembrowsing, params={'Action': 'systembrowsing'}")
        self.wait()
        
        with self.assertLogs(log, logging.INFO) as cm:
            self.eh._mqttSubscriber.mockEvent('gamelistbrowsing', evParams)
            self.wait()
            self.assertEqual(cm.output[0], 'INFO:dynquee:generate action gamelistbrowsing')
            self.assertEqual(cm.output[2], "INFO:dynquee:action=gamelistbrowsing, params={'SystemId': 'snes', 'GamePath': '/path/to/mario.zip', 'IsFolder': '0', 'Action': 'gamelistbrowsing'}")
        self.wait()

        self.eh._mqttSubscriber.stop()


if __name__ == '__main__':
    setupTestConfig()
    suite: unittest.TestSuite = unittest.TestLoader().loadTestsFromTestCase(
        testEventHandler
    )
    result: unittest.TestResult = unittest.TextTestRunner().run(suite)
