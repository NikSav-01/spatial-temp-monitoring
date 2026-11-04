from time import sleep, localtime

from machine import Pin, SoftI2C

# I2C Setup
i2c = SoftI2C(scl=Pin(1), sda=Pin(0), freq=100_000)
LCD_ADDR = 39


# LCD Command Helper
def write(cmd, rs=0, light=0x08):
    # RS=0 for cmd, RS=1 for data
    high_nibble = (cmd & 0xF0) | (rs << 0) | 0x04 | light
    low_nibble = ((cmd << 4) & 0xF0) | (rs << 0) | 0x04 | light
    lcd_data = bytes(
        [
            high_nibble,
            high_nibble & 0xFB,
            low_nibble,
            low_nibble & 0xFB,
        ]
    )
    try:
        i2c.writeto(LCD_ADDR, lcd_data)
    except OSError:
        if reconnect():
            try:
                i2c.writeto(LCD_ADDR, lcd_data)
            except OSError:
                return

    # Clear Display (0x01) and Return Home (0x02) need >1.5ms
    if cmd in (0x01, 0x02) and rs == 0:
        sleep(0.003)
    else:
        sleep(0.001)


def init(retry=False):
    write(0x33, light=0x00)  # Initialize
    sleep(0.01)
    write(0x32, light=0x00)  # 4-bit mode
    sleep(0.005)
    write(0x28, light=0x00)  # 2 lines, 5x8 font
    sleep(0.001)
    write(0x0C, light=0x00)  # Display ON, backlight ON
    write(0x01, light=0x00)  # Clear screen
    sleep(0.005)


def print_text(text, line=0, col=0, light=0x08):
    line_offsets = [0x00, 0x40, 0x14, 0x54]
    write(0x80 | (line_offsets[line] + col), light=light)  # Set cursor
    for char in text:
        write(ord(char), rs=1, light=light)  # Write char


def reconnect():
    global i2c
    try:
        i2c = SoftI2C(scl=Pin(1), sda=Pin(0), freq=100_000)
        sleep(0.05)
        init(retry=False)
        return True
    except OSError:
        t = localtime()
        timestamp = f"[{t[3]:02d}:{t[4]:02d}]"
        with open("log.txt", "a") as f:
            f.write(f"{timestamp} LCD Reconnect Failed")
        return False


init()
