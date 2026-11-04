import time

import ds18x20
import onewire
import ubinascii
from machine import Pin

import lcd

ow_pin = Pin(13, Pin.PULL_UP)
ow = onewire.OneWire(ow_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()

sensor_ids_file = 'temperature_sensor_IDs.txt'
sensor_ids = []
try:
    with open(sensor_ids_file, "r") as f: 
        sensor_ids = [line.strip() for line in f if line.strip()]
except OSError as e:
    print("Error opening temperature_sensor_IDs.txt:", e)


# If the file doesn't exist or is empty
if not sensor_ids:
    print(f"'{sensor_ids_file}' is missing or empty. Scanning OneWire bus")
    sensor_ids = [ubinascii.hexlify(rom).decode() for rom in roms]

    if sensor_ids:
        try:
            with open(sensor_ids_file, "w") as f:
                for rom_id in sensor_ids:
                    f.write(rom_id + "\n")
            print(f"Saved {len(sensor_ids)} sensor ID(s) to {sensor_ids_file}")
            print("Must order IDs to pyshical spatial positioning.")
        except OSError as e:
            print(f"Error saving to {sensor_ids_file}:", e)
    else:
        print("No DS18B20 sensors found during scan.")

print("Active Sensor IDs:", sensor_ids)




def c_2_f(c):
    return (c * 9 / 5) + 32


def read_temperatures(show=True, unit="c"):
    try:
        ds.convert_temp()
        if show:
            lcd.write(0x01)
            lcd.print_text("MEASURING", 1, 5)
        time.sleep_ms(1000)  # Wait for conversion
        temps = {}
        for rom in roms:
            rom_str = ubinascii.hexlify(rom).decode()
            temps[rom_str] = ds.read_temp(rom)

        ordered_temps = [0] * 5

        for i, rom_id in enumerate(sensor_ids[:5]):
            ordered_temps[i] = temps.get(rom_id, 0)

        if unit == "f":
            ordered_temps = [c_2_f(i) for i in ordered_temps]

        return ordered_temps
    except OSError as e:
        print("DS18B20 read error:", e)
        return None


def read_humidity(hum_sens_list, units="c"):
    read_data = []
    for hum_sens in hum_sens_list:
        try:
            hum_sens.measure()

            temp = hum_sens.temperature()  # Temperature in Celsius
            humidity = hum_sens.humidity()  # Humidity percentage (%)

            if units == "f":
                temp = c_2_f(temp)

            read_data.append([temp, humidity])

        except OSError as e:
            print("DHT22 read error:", e)

    # If one sensor has a reading error,
    # just duplicate the working sensor's data
    if len(read_data) == 0:
        return None
    elif len(read_data) == 1:
        return(read_data * 2)
    else:
        return(read_data)
