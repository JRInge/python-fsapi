import pytest
import xml.etree.ElementTree as ET
from fsapi import FSAPI


@pytest.fixture
def xml_test_data():
    return ET.fromstring('<fsapiResponse>\
        <status>FS_OK</status>\
        <value><c8_array>My Radio</c8_array></value>\
        <field name="streamable"><u8>0</u8></field>\
        </fsapiResponse>')


class TestHelperMethods():

    def test_unpack_xml_handles_l1_value(self, xml_test_data):
        assert FSAPI.unpack_xml(xml_test_data, 'status') == 'FS_OK'

    def test_unpack_xml_handles_l2_value(self, xml_test_data):
        assert FSAPI.unpack_xml(xml_test_data, 'value/c8_array') == 'My Radio'

    def test_unpack_xml_handles_None(self, xml_test_data):
        assert FSAPI.unpack_xml(None, 'status') is None

    def test_maybe_handles_None(self):
        assert FSAPI.maybe(None, int) is None

    def test_maybe_handles_str2int(self):
        assert FSAPI.maybe("1", int) == 1

    def test_maybe_accepts_lambda(self):
        assert FSAPI.maybe(1, lambda x: str(x)) == "1"
