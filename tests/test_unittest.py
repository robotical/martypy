from martypy.WebSocketLink import WebSocketLink
import unittest

class Test_TestWebSocketLink(unittest.TestCase):

    def test_frameLength7bit(self):
        wsl = WebSocketLink()
        wsl.curInputData += bytes.fromhex("817d")
        headerValid, fin, opcode, mask, frameLen, curPos = wsl.extract_header_info()
        self.assertEqual(headerValid, True)
        self.assertEqual(fin, True)
        self.assertEqual(opcode, 1)
        self.assertEqual(mask, False)
        self.assertEqual(frameLen, 125)
        self.assertEqual(curPos, 2)

    def test_frameLength16bit(self):
        wsl = WebSocketLink()
        wsl.curInputData += bytes.fromhex("827eaaaa")
        headerValid, fin, opcode, mask, frameLen, curPos = wsl.extract_header_info()
        self.assertEqual(headerValid, True)
        self.assertEqual(fin, True)
        self.assertEqual(opcode, 2)
        self.assertEqual(mask, False)
        self.assertEqual(frameLen, 43690)
        self.assertEqual(curPos, 4)

    def test_frameLength64bit(self):
        wsl = WebSocketLink()
        wsl.curInputData += bytes.fromhex("8a7f00000000aaaaaaaa")
        headerValid, fin, opcode, mask, frameLen, curPos = wsl.extract_header_info()
        self.assertEqual(headerValid, True)
        self.assertEqual(fin, True)
        self.assertEqual(opcode, 10)
        self.assertEqual(mask, False)
        self.assertEqual(frameLen, 2863311530)
        self.assertEqual(curPos, 10)





