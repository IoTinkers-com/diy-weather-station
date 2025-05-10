from machine import Pin, SoftI2C
from time import sleep

class LCD:
    def __init__(self, scl_pin=22, sda_pin=21, addr=0x27):
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.addr = addr
        self.init_display()
    
    def send_command(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytes([0x08 | (cmd & 0xF0)]))
            sleep(0.005)
            self.i2c.writeto(self.addr, bytes([0x08 | ((cmd & 0xF0) | 0x04)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x08 | (cmd & 0xF0)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x08 | ((cmd & 0x0F) << 4)]))
            sleep(0.005)
            self.i2c.writeto(self.addr, bytes([0x08 | (((cmd & 0x0F) << 4) | 0x04)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x08 | ((cmd & 0x0F) << 4)]))
            sleep(0.001)
        except Exception as e:
            print(f"Error en comando {hex(cmd)}: {e}")

    def send_data(self, data):
        try:
            self.i2c.writeto(self.addr, bytes([0x09 | (data & 0xF0)]))
            sleep(0.005)
            self.i2c.writeto(self.addr, bytes([0x09 | ((data & 0xF0) | 0x04)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x09 | (data & 0xF0)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x09 | ((data & 0x0F) << 4)]))
            sleep(0.005)
            self.i2c.writeto(self.addr, bytes([0x09 | (((data & 0x0F) << 4) | 0x04)]))
            sleep(0.001)
            self.i2c.writeto(self.addr, bytes([0x09 | ((data & 0x0F) << 4)]))
            sleep(0.001)
        except Exception as e:
            print(f"Error en datos {hex(data)}: {e}")

    def init_display(self):
        commands = [0x03, 0x03, 0x03, 0x02, 0x28, 0x08, 0x01, 0x06, 0x0C]
        for cmd in commands:
            self.send_command(cmd)
            sleep(0.1)

    def set_cursor(self, line, pos):
        if line == 0:
            self.send_command(0x80 + pos)
        else:
            self.send_command(0xC0 + pos)

    def write(self, text):
        for char in text:
            self.send_data(ord(char))
            sleep(0.001)

    def clear(self):
        self.send_command(0x01)
        sleep(0.002)