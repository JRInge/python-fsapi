## python-fsapi
![](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8-informational?style=flat-square&logo=Python) [![](https://img.shields.io/travis/com/JRInge/python-fsapi?style=flat-square)](https://travis-ci.com/github/JRInge/python-fsapi)

Python implementation of the Frontier Silicon API for digital radios and streaming devices.
- This project was started in order to embed Frontier Silicon devices in Home Assistant (https://home-assistant.io/)
- Inspired by:
  - https://github.com/flammy/fsapi/
  - https://github.com/tiwilliam/fsapi
  - https://github.com/zhelev/python-fsapi

The current fork has been developed to run on [QPython](https://play.google.com/store/apps/details?id=org.qpython.qpy), to allow scripted control of digital radios from an Android phone.  The @zhelev version was dependent on `lxml`, which does not work on QPython as it relies on native libraries that have not been ported to Android.  This fork uses the standard `xml.etree` library, which is packaged with QPython.

Type checking annotations have been added for use with `mypy`, to make the code more robust and to make it easier to avoid errors in the porting process from `lxml` to `etree`.

Required python libs:
  - requests (install on QPython using `pip3`)
