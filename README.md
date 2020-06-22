# python-fsapi
Python implementation of the Frontier Silicon API
- This project was started in order to embed Frontier Silicon devices in Home Assistant (https://home-assistant.io/)
- Inspired by:
 - https://github.com/flammy/fsapi/
 - https://github.com/tiwilliam/fsapi
 - https://github.com/p2baron/fsapi
 - https://github.com/zhelev/python-fsapi

This fork is being developed to run on QPython3L. The intent is to add type checking annotations for use with `mypy`, improve the code to make error handling more robust, then adapt it to remove the dependency on `lxml`, which doesn't seem to work on QPython.

Required python libs:
  - requests
  - lxml (had to install it through apt-get, pip3 did not work)

