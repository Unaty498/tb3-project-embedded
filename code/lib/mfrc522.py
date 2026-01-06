from machine import Pin, SPI
from os import uname

class MFRC522:
    DEBUG = False
    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

    def __init__(self, spi, gpioRst, gpioSda):
        self.spi = spi
        self.rst = Pin(gpioRst, Pin.OUT)
        self.cs = Pin(gpioSda, Pin.OUT)
        self.cs.value(1)
        self.rst.value(0)
        self.init()

    def _wreg(self, reg, val):
        self.cs.value(0)
        self.spi.write(b'%c' % int((reg << 1) & 0x7e))
        self.spi.write(b'%c' % int(val))
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self.spi.write(b'%c' % int(((reg << 1) & 0x7e) | 0x80))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):
        recv = []
        bits = 0
        irq_en = 0x00
        wait_irq = 0x00
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break

        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR

                if cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR

        return stat, recv, bits

    def _crc(self, data):
        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 255
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def init(self):
        self.rst.value(1)
        self._wreg(0x01, 0x0F)
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])

        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self):
        ser_chk = 0
        ser = [0x93, 0x20]

        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def select_tag(self, uid):
        backData = []
        buf = [0x93, 0x70] + uid[:4]
        buf += [self._crc(buf[:6])[0], self._crc(buf[:6])[1]] # Checksum
        (status, backData, backLen) = self._tocard(0x0C, buf)
        
        # On verifie juste que la communication est OK et qu'on a recu le SAK (24 bits = 3 octets avec CRC)
        if (status == self.OK) and (backLen == 0x18):
            return self.OK, backData[0] # Renvoie (Status, SAK)
        else:
            return self.ERR, 0

    def auth(self, mode, addr, sect, ser):
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def stop_crypto(self):
        self._cflags(0x08, 0x08)

    def read(self, addr):
        (stat, recv, _) = self._tocard(0x0C, [0x30, addr, 0, 0]) # 0x30 is READ command
        if stat == self.OK:
             if len(recv) == 16:
                 return recv
        return None

    def write(self, addr, data):
        buf = [0xA0, addr] + self._crc([0xA0, addr])
        (stat, recv, bits) = self._tocard(0x0C, buf)

        if (stat != self.OK) or (bits != 4) or ((recv[0] & 0x0F) != 0x0A):
            stat = self.ERR
        else:
            buf = []
            for i in range(16):
                buf.append(data[i])
            buf += self._crc(buf)
            (stat, recv, bits) = self._tocard(0x0C, buf)
            if (stat != self.OK) or (bits != 4) or ((recv[0] & 0x0F) != 0x0A):
                stat = self.ERR
        return stat

    def antenna_on(self):
        temp = self._rreg(0x14)
        if ~(temp & 0x03):
            self._sflags(0x14, 0x03)

    def antenna_off(self):
        self._cflags(0x14, 0x03)