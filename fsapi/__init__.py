"""
Support for interaction with Frontier Silicon Devices
For example internet radios from: Medion, Hama, Auna, ...
"""
import requests
import logging
import traceback
from lxml import objectify  # type: ignore
from typing import Any, Dict, List, Optional, Union, cast


DataItem = Union[str, int]


class FSAPI(object):

    DEFAULT_TIMEOUT_IN_SECONDS = 1

    PLAY_STATES = {
        0: 'stopped',
        1: 'unknown',
        2: 'playing',
        3: 'paused',
    }

    def __init__(self, fsapi_device_url: str, pin: str, timeout: int = DEFAULT_TIMEOUT_IN_SECONDS):
        self.pin = pin
        self.sid: Optional[str] = None
        self.webfsapi: Optional[str] = None
        self.fsapi_device_url = fsapi_device_url
        self.timeout = timeout

        self.webfsapi = self.get_fsapi_endpoint()
        self.sid = self.create_session()

    def get_fsapi_endpoint(self) -> str:
        endpoint = requests.get(self.fsapi_device_url, timeout = self.timeout)
        doc = objectify.fromstring(endpoint.content)
        return cast(str, doc.webfsapi.text)

    def create_session(self) -> Optional[str]:
        doc = self.call('CREATE_SESSION')
        return cast(str, doc.sessionId.text)

    def call(self, path: str, extra: Optional[Dict[str, DataItem]] = None) -> Optional[objectify.ObjectifiedElement]:
        """Execute a frontier silicon API call."""
        try:
            if not self.webfsapi:
                raise Exception('No server found')

            if type(extra) is not dict:
                extra = dict()

            params: Dict[str, DataItem] = dict(
                pin=self.pin,
                sid=self.sid,
            )

            params.update(**cast(Dict[str, Union[int, str]],extra)) # By now, this is definitely a Dict

            result = requests.get('%s/%s' % (self.webfsapi, path), params=params, timeout = self.timeout)
            if result.status_code == 404:
                return None

            return objectify.fromstring(result.content)
        except Exception as e:
            logging.error('FSAPI Exception: ' + traceback.format_exc())

        return None

    def __del__(self) -> None:
        self.call('DELETE_SESSION')

    # Handlers

    def handle_get(self, item: str) -> Optional[objectify.ObjectifiedElement]:
        return self.call('GET/{}'.format(item))

    def handle_set(self, item: str, value: Any) -> Optional[bool]:
        doc = self.call('SET/{}'.format(item), dict(value=value))
        if doc is None:
            return None

        return cast(str, doc.status) == 'FS_OK'

    def handle_text(self, item: str) -> Optional[str]:
        doc = self.handle_get(item)
        if doc is None:
            return None

        return cast(str, doc.value.c8_array.text) or None

    def handle_int(self, item: str) -> Optional[int]:
        doc = self.handle_get(item)
        if doc is None:
            return None

        return int(doc.value.u8.text) or None

    # returns an int, assuming the value does not exceed 8 bits
    def handle_long(self, item: str) -> Optional[int]:
        doc = self.handle_get(item)
        if doc is None:
            return None

        return int(doc.value.u32.text) or None

    def handle_list(self, item: str) -> List[Dict[str, Optional[DataItem]]]:
        doc = self.call('LIST_GET_NEXT/'+item+'/-1', dict(
            maxItems=100,
        ))

        if doc is None:
            return []

        if not doc.status == 'FS_OK':
            return []
        ret: List[Dict[str, Optional[DataItem]]] = list()
        for item in list(doc.iterchildren('item')):
            temp: Dict[str, Optional[DataItem]] = dict()
            for field in list(item.iterchildren()):
                temp[field.get('name')] = list(field.iterchildren()).pop()
            if 'key' in item.attrib:
                temp['key'] = item.attrib.get('key')
            ret.append(temp)

        return ret

    def collect_labels(self, items: List[Dict[str, Any]]) -> List[str]:
        if items is None:
            return []

        return [str(item['label']) for item in items if item['label']]

    # Properties
    @property
    def play_status(self) -> Optional[str]:
        status = self.handle_int('netRemote.play.status')
        return self.PLAY_STATES.get(status)

    @property
    def play_info_name(self) -> Optional[str]:
        return self.handle_text('netRemote.play.info.name')

    @property
    def play_info_text(self) -> Optional[str]:
        return self.handle_text('netRemote.play.info.text')

    @property
    def play_info_artist(self) -> Optional[str]:
        return self.handle_text('netRemote.play.info.artist')

    @property
    def play_info_album(self) -> Optional[str]:
        return self.handle_text('netRemote.play.info.album')

    @property
    def play_info_graphics(self) -> Optional[str]:
        return self.handle_text('netRemote.play.info.graphicUri')

    @property
    def volume_steps(self) -> Optional[int]:
        return self.handle_int('netRemote.sys.caps.volumeSteps')

    # Read-write

    # 1=Play; 2=Pause; 3=Next (song/station); 4=Previous (song/station)
    def play_control(self, value: int) -> Optional[bool]:
        return self.handle_set('netRemote.play.control', value)

    def play(self) -> Optional[bool]:
        return self.play_control(1)

    def pause(self) -> Optional[bool]:
        return self.play_control(2)

    def forward(self) -> Optional[bool]:
        return self.play_control(3)

    def rewind(self) -> Optional[bool]:
        return self.play_control(4)

    # Volume
    @property
    def volume(self) -> Optional[int]:
        return self.handle_int('netRemote.sys.audio.volume')

    @volume.setter
    def volume(self, value: int) -> Optional[bool]:
        return self.handle_set('netRemote.sys.audio.volume', value)

    # Friendly name
    @property
    def friendly_name(self) -> Optional[str]:
        return self.handle_text('netRemote.sys.info.friendlyName')

    @friendly_name.setter
    def friendly_name(self, value: Any) -> Optional[bool]:
        return self.handle_set('netRemote.sys.info.friendlyName', value)

    # Mute
    @property
    def mute(self) -> bool:
        return bool(self.handle_int('netRemote.sys.audio.mute'))

    @mute.setter
    def mute(self, value: Any = False) -> Optional[bool]:
        return self.handle_set('netRemote.sys.audio.mute', int(value))

    # Power
    @property
    def power(self) -> bool:
        return bool(self.handle_int('netRemote.sys.power'))

    @power.setter
    def power(self, value: Any = False) -> Optional[bool]:
        return self.handle_set('netRemote.sys.power', int(value))

    # Modes
    @property
    def modes(self) -> List[Dict[str, Optional[DataItem]]]:
        return self.handle_list('netRemote.sys.caps.validModes')

    @property
    def mode_list(self) -> List[str]:
        return self.collect_labels(self.modes)

    @property
    def mode(self) -> str:
        mode = None
        int_mode = self.handle_long('netRemote.sys.mode')
        if int_mode is not None:
            for temp_mode in self.modes:
                if temp_mode['key'] == str(int_mode):
                    mode = temp_mode['label']
        return str(mode)

    @mode.setter
    def mode(self, value: str) -> None:
        for temp_mode in self.modes:
            if 'label' in temp_mode and 'key' in temp_mode:
                if temp_mode['label'] == value:
                    mode = temp_mode['key']
                    if mode is not None:
                        self.handle_set('netRemote.sys.mode', mode)

    @property
    def duration(self) -> Optional[int]:
        return self.handle_long('netRemote.play.info.duration')
