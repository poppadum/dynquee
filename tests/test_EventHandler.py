#!/usr/bin/env python3

"""Integration tests for dynquee.EventHandler class
    uses unittest framework with time delays
"""

import unittest
import logging
import time
import os
from threading import Thread
from typing import Optional, Dict, List
from dynquee import EventHandler, MQTTSubscriber, MediaManager, Slideshow, log, config

log.setLevel(logging.INFO)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = f"{os.path.dirname(__file__)}/test_dynquee.ini"
    config.read(configFile)
    log.info("loaded test config file: %s", configFile)


class MockMQTTSubscriber(MQTTSubscriber):
    '''Mocked MockMQTTSubscriber: can be told what actions to fire'''
    # _VALID_ACTIONS = ['systembrowsing','gamelistbrowsing','rungame','endgame']
    def __init__(self):
        self._disconnect = False
        self._nextEvent = {}
        self._nextEventProcessed = True

    def __del__(self):
        pass
    def start(self, *_args):
        pass
    def _onConnect(self, client, user, flags, rc: int):
        pass

    def _onDisconnect(self, client, userdata, rc: int):
        pass

    def stop(self):
        self._disconnect = True

    def getEvent(self, checkInterval: float = 5.0) -> Optional[str]:
        # wait until we have an event or disconnect
        while True:
            if self._disconnect:
                break
            if not self._nextEventProcessed:
                break
            time.sleep(0.1)
        if self._disconnect:
            return None
        action:str = self._nextEvent.get('action')
        log.info("generate action %s", action)
        # mark event processed
        self._nextEventProcessed = True
        return action

    def getEventParams(self) -> Dict[str, str]:
        evParams = self._nextEvent.get('evParams')
        evParams['Action'] = self._nextEvent.get('action')
        log.info("generate evParams %s", evParams)
        return evParams

    def mockEvent(self, action: str, evParams: Dict[str, str]):
        """Mock an event occurring"""
        self._nextEvent = {
            'action': action,
            'evParams': evParams
        }
        self._nextEventProcessed = False


class MockSlideshow(Slideshow):
    '''Mock Slideshow: does not launch any subprocess'''
    def _runCmd(self, cmd: List[str], waitForExit: bool = False) -> bool:
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
        # mock arcade meta-system properties
        self._arcadeSystemEnabled: bool = False


class TestEventHandler(unittest.TestCase):
    """EventHandler end-to-end tests"""

    _EV_PARAMS = {
        'SystemId': 'snes',
        'GamePath': '/path/to/mario.zip',
        'IsFolder': '0'
    }

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

    @classmethod
    def wait(cls):
        '''time delay to let event propagate'''
        time.sleep(0.25)

    def fireEventAndAssert(self,
        action: str,
        evParams: Dict[str, str],
        expectedOutput: Dict[str, str]
    ):
        """Fire an event and check the log output is as expected"""
        with self.assertLogs(log, logging.INFO) as cmd:
            self.eh._mqttSubscriber.mockEvent(action, evParams)
            self.wait()
            for index, logStr in expectedOutput.items():
                self.assertEqual(cmd.output[int(index)], logStr)
        self.wait()


    def testEventHandlerSystem(self):
        """Test `systembrowsing` and `gamelistbrowsing` events produce expected log output"""
        self.fireEventAndAssert(
            action = 'systembrowsing',
            evParams = {},
            expectedOutput = {
                '0': 'INFO:dynquee:generate action systembrowsing',
                '2': "INFO:dynquee:event params={'Action': 'systembrowsing'}"
            }
        )

        self.fireEventAndAssert(
            action = 'gamelistbrowsing',
            evParams = self._EV_PARAMS,
            expectedOutput = {
                '0': 'INFO:dynquee:generate action gamelistbrowsing',
                '2': "INFO:dynquee:event params={'SystemId': 'snes', "
                     "'GamePath': '/path/to/mario.zip', 'IsFolder': '0', "
                     "'Action': 'gamelistbrowsing'}"
            }
        )


    def testEventHandlerSleepWakeup(self):
        """Test `wakeup` event repeats event before sleep and restores state"""
        # send normal event first
        self.fireEventAndAssert(
            action = 'systembrowsing',
            evParams = self._EV_PARAMS,
            expectedOutput = {
                '0': 'INFO:dynquee:generate action systembrowsing',
                '2': "INFO:dynquee:event params={'SystemId': 'snes', "
                     "'GamePath': '/path/to/mario.zip', 'IsFolder': '0', "
                     "'Action': 'systembrowsing'}"
            }
        )

        # test sleep
        self.fireEventAndAssert(
            action = 'sleep',
            evParams = {},
            expectedOutput = {
                '0': 'INFO:dynquee:generate action sleep',
                '2': "INFO:dynquee:event params={'Action': 'sleep'}"
            }
        )
        # check state before sleep recorded
        self.assertEqual(self.eh._stateBeforeSleep.action, 'systembrowsing')
        self.assertEqual(self.eh._stateBeforeSleep.system, 'snes')
        self.assertEqual(self.eh._stateBeforeSleep.game, '/path/to/mario.zip')
        self.assertFalse(self.eh._stateBeforeSleep.isFolder)

        # test wakeup
        self.fireEventAndAssert(
            action = 'wakeup',
            evParams = {},
            expectedOutput = {
                '0': 'INFO:dynquee:generate action wakeup',
                '2': "INFO:dynquee:event params={'Action': 'wakeup'}"
            }
        )
        # check state before sleep restored
        self.assertEqual(self.eh._currentState.action, 'systembrowsing')
        self.assertEqual(self.eh._currentState.system, 'snes')
        self.assertEqual(self.eh._currentState.game, '/path/to/mario.zip')
        self.assertFalse(self.eh._currentState.isFolder)

        # test normal event after wakeup
        self.fireEventAndAssert(
            action = 'systembrowsing',
            evParams = {'SystemId': 'megadrive'},
            expectedOutput = {
                '0': 'INFO:dynquee:generate action systembrowsing',
                '2': "INFO:dynquee:event "
                     "params={'SystemId': 'megadrive', 'Action': 'systembrowsing'}"
            }
        )
        # check state
        self.assertEqual(self.eh._currentState.action, 'systembrowsing')
        self.assertEqual(self.eh._currentState.system, 'megadrive')
        self.assertEqual(self.eh._currentState.game, '')
        self.assertFalse(self.eh._currentState.isFolder)




if __name__ == '__main__':
    setupTestConfig()
    suite: unittest.TestSuite = unittest.TestLoader().loadTestsFromTestCase(
        TestEventHandler
    )
    result: unittest.TestResult = unittest.TextTestRunner().run(suite)
