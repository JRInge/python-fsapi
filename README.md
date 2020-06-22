# python-fsapi
Python implementation of the Frontier Silicon API
- This project was started in order to embed Frontier Silicon devices in Home Assistant (https://home-assistant.io/)
- Inspired by:
 - https://github.com/flammy/fsapi/
 - https://github.com/tiwilliam/fsapi
 - https://github.com/p2baron/fsapi
 - https://github.com/zhelev/python-fsapi

Required python libs:
  - requests
  - lxml (had to install it through apt-get, pip3 did not work)

Usage
=====

```python
from fsapi import FSAPI

URL = 'http://192.168.1.39:80/device'
PIN = 1234
TIMEOUT = 1 # in seconds

fs = FSAPI(URL, PIN, TIMEOUT)
print('Name: %s' % fs.friendly_name)
print('Mute: %s' % fs.mute)
print('Mode: %s' % fs.mode)
print('Modes: %s' % fs.modes)
print('Power: %s' % fs.power)
print('Volume steps: %s' % fs.volume_steps)
print('Volume: %s' % fs.volume)
print('Play status: %s' % fs.play_status)
print('Track name: %s' % fs.play_info_name)
print('Track text: %s' % fs.play_info_text)
print('Artist: %s' % fs.play_info_artist)
print('Album: %s' % fs.play_info_album)
print('Graphics: %s' % fs.play_info_graphics)
