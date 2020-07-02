"""
Support for interaction with Frontier Silicon Devices
For example internet radios from: Medion, Hama, Auna, ...
"""
import requests
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union


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

    @staticmethod
    def unpack_xml(root: Optional[ET.Element], key: str) -> Optional[str]:
        if root:
            element = root.find(key)
            if hasattr(element, "text"):
                return str(element.text)  # type: ignore
        return None

    def get_fsapi_endpoint(self) -> str:
        try:
            endpoint = requests.get(self.fsapi_device_url,
                                    timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise TimeoutError("FSAPI could not get a response from {}"
                               .format(self.fsapi_device_url))
        except requests.exceptions.RequestException:
            raise ConnectionError("FSAPI could not connect to {}"
                                  .format(self.fsapi_device_url))

        doc = ET.fromstring(endpoint.content)
        api = doc.find("webfsapi")
        if api is not None and api.text:
            return api.text
        else:
            raise ConnectionRefusedError("FSAPI endpoint not found at {}"
                                         .format(self.fsapi_device_url))

        return self.unpack_xml(self.call('CREATE_SESSION'), "sessionId")

    def create_session(self) -> Optional[str]:
        return self.unpack_xml(self.call('CREATE_SESSION'), "sessionId")

    def call(self,
             path: str,
             extra: Optional[Dict[str, DataItem]] = None)\
            -> Optional[ET.Element]:
        """Execute a frontier silicon API call."""
        if not self.webfsapi:
            raise RuntimeError("FSAPI not successfully initialised.")

        params: Dict[str, DataItem] = dict(pin=self.pin)
        if self.sid:
            params.update(sid=self.sid)
        if extra is not None:
            params.update(**extra)

        result = requests.get('%s/%s' % (self.webfsapi, path),
                              params=params,
                              timeout=self.timeout)
        if result.status_code == 403:
            raise PermissionError("FSAPI access denied - incorrect PIN")
        if result.status_code == 404:
            # Bad session ID or service endpoint
            logging.warn("FSAPI service call failed to %s/%s"
                         % (self.webfsapi, path))
            return None

        doc = ET.fromstring(result.content)
        status = self.unpack_xml(doc, "status")
        if status == "FS_NODE_DOES_NOT_EXIST":
            raise NotImplementedError("FSAPI service %s not implemented at %s."
                                      % (path, self.webfsapi))
        if status == "FS_OK":
            return doc

        logging.warn("Unexpected FSAPI status %s" % status)
        return None

    # Handlers

    def handle_get(self, item: str) -> Optional[ET.Element]:
        return self.call('GET/{}'.format(item))

    def handle_set(self, item: str, value: Any) -> Optional[bool]:
        status = self.unpack_xml(self.call('SET/{}'.format(item),
                                 dict(value=value)), "status")
        if status is None:
            return None

        return status == 'FS_OK'

    def handle_text(self, item: str) -> Optional[str]:
        return self.unpack_xml(self.handle_get(item), "value/c8_array")

    def handle_int(self, item: str) -> Optional[int]:
        val = self.unpack_xml(self.handle_get(item), "value/u8")
        if val is None:
            return None

        return int(val) or None

    # returns an int, assuming the value does not exceed 8 bits
    def handle_long(self, item: str) -> Optional[int]:
        val = self.unpack_xml(self.handle_get(item), "value/u32")
        if val is None:
            return None

        return int(val) or None

    def handle_list(self, item: str) -> List[Dict[str, Optional[DataItem]]]:
        def handle_field(field: ET.Element) -> Tuple[str, Optional[DataItem]]:
            # TODO: Handle other field types
            if 'name' in field.attrib:
                id = field.attrib['name']
                s = self.unpack_xml(field, 'c8_array')
                v = self.unpack_xml(field, 'u8')
                if v is not None:
                    return (id, int(v))
                return (id, s)
            return ("", None)

        def handle_item(item: ET.Element) -> Dict[str, Optional[DataItem]]:
            ret = dict(map(handle_field, item.findall('field')))
            if 'key' in item.attrib:
                ret['key'] = item.attrib['key']
            return ret

        doc = self.call('LIST_GET_NEXT/'+item+'/-1', dict(
            maxItems=100,
        ))

        if doc is None:
            return []

        status = self.unpack_xml(doc, "status")
        if not status == 'FS_OK':
            return []

        return list(map(handle_item, doc.findall('item')))

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
