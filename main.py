import sys
import time
from time import sleep

import dht
from machine import RTC, Pin

import display
import lcd
import sensors
import storage

# Buttons
# Button 1, Button 2, etc.
b1 = Pin(2, Pin.IN, Pin.PULL_UP)
b2 = Pin(3, Pin.IN, Pin.PULL_UP)
b3 = Pin(4, Pin.IN, Pin.PULL_UP)
b4 = Pin(5, Pin.IN, Pin.PULL_UP)

# Button 1 Pressed, Button 2 Pressed, etc.
b1_pressed = False
b2_pressed = False
b3_pressed = False
b4_pressed = False

button_selection = "normal"

# Temperature sensor initial readings
temps = sensors.read_temperatures()
if temps is not None:
    # Order: Front, Back, Hall, Room, Light
    high_temps = list(temps)
    low_temps = list(temps)
else:
    lcd.write(0x01)
    lcd.print_text("Error Reading Temp", 0, 1)
    lcd.print_text("Initial Reading", 1, 2)

# LCD Display
clear_LCD = time.ticks_ms()
screen_timeout = 1000
screen_on = True

# Password init
secret_settings_passcode, settings_passcode = storage.load_passwords()
passcode = []

# Motion sensors and LED lights
bot_motion_sens = Pin(6, Pin.IN, Pin.PULL_DOWN)
mid_motion_sens = Pin(7, Pin.IN, Pin.PULL_DOWN)
top_motion_sens = Pin(8, Pin.IN, Pin.PULL_DOWN)

bot_led = Pin(10, Pin.OUT)  # RED
mid_led = Pin(12, Pin.OUT)  # BLUE
top_led = Pin(11, Pin.OUT)  # YELLOW

bot_sens_prev = 0
mid_sens_prev = 0
top_sens_prev = 0

# Relay Switch
# sensor_switch.value() == 0, Sensors on
sensor_switch = Pin(14, Pin.OUT)

# Door variables
# doorButton.value() == 0, Open Door
door_button = Pin(9, Pin.IN, Pin.PULL_UP)
door_open = True
door_preset_time = time.ticks_ms()

door_reset_button = Pin(16, Pin.IN, Pin.PULL_UP)
door_reset_btn_pressed = False
door_reset = False
door_reset_press_time = time.ticks_ms()
door_preset_used = True

# Humidity sensors and Relay
# humidity_switch.value() == 1, electric plug off
humidity_switch = Pin(15, Pin.OUT)

humidity_sensor_1 = dht.DHT22(Pin(17))  # light
humidity_sensor_2 = dht.DHT22(Pin(18))  # door

humidity_state = 0
humidity_off_percent = 50
checked_humidity = False

saved_humidity = [0] * 24
set_saved_humidity = False
hum_selected_hour = 0
hum_hours_ago = 0

hum_sensor_list = [humidity_sensor_1, humidity_sensor_2]
humidity_data = sensors.read_humidity(hum_sensor_list)
if humidity_data is not None:
    hum_1 = humidity_data[0][1]
    hum_2 = humidity_data[1][1]
    max_hum = max(hum_1, hum_2)
    min_hum = min(hum_1, hum_2)
    mean_hum = (hum_1 + hum_2) / 2
else:
    max_hum = 0
    min_hum = 100
    mean_hum = 0

# Load history
history_records = storage.load_history()

# Misc
temp_units = "f"
led_main = False
reset_midnight_temps = True


def handle_normal():
    global clear_LCD, screen_timeout, screen_on, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global led_main, door_reset, passcode

    if b1.value() == 0 and not b1_pressed:  # LEDs & Sensor OFF
        b1_pressed = True
        led_main = False
        door_reset = False
        sensor_switch.value(1)  # Sensor OFF

    if b2.value() == 0 and not b2_pressed:
        b2_pressed = True
        display.main_temps(temp_units, high_temps, low_temps)
        clear_LCD = time.ticks_ms()
        screen_timeout = 20000
        screen_on = True
        button_selection = "temperatures"

    if b3.value() == 0 and not b3_pressed:  # Humidity
        b3_pressed = True
        display.humidity(
            humidity_sensor_1,
            humidity_sensor_2,
            humidity_state,
            humidity_off_percent,
            temp_units,
        )
        clear_LCD = time.ticks_ms()
        screen_timeout = 20000
        screen_on = True
        button_selection = "humidity"

    if b4.value() == 0 and not b4_pressed:  # Settings
        b4_pressed = True
        passcode = []
        lcd.write(0x01)
        lcd.print_text("Settings", 0, 6)
        lcd.print_text("Password:", 1, 6)
        clear_LCD = time.ticks_ms()
        screen_timeout = 6000
        screen_on = True
        button_selection = "passcode"


def handle_temperatures():
    global clear_LCD, screen_timeout, screen_on, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global current_viewing_day

    if b1.value() == 0 and not b1_pressed:  # Legend for Temperature Screen
        b1_pressed = True
        display.temp_legend()
        clear_LCD = time.ticks_ms()
        button_selection = "tempLegend"

    # Reset Timer & Remeasure for Temp Screen
    if b2.value() == 0 and not b2_pressed:
        b2_pressed = True
        display.main_temps(temp_units, high_temps, low_temps)
        clear_LCD = time.ticks_ms()

    if b3.value() == 0 and not b3_pressed:  # Show history of temp
        b3_pressed = True
        # Add inital screen
        if history_records == []:  # No Records
            lcd.write(0x01)
            lcd.print_text("No Records Yet", 0, 3)
            screen_timeout = 2000
            screen_on = True
        else:
            current_viewing_day = -1
            display.history(
                history_records[current_viewing_day],
                current_viewing_day,
                temp_units,
            )
            screen_timeout = 8000
            screen_on = True
            button_selection = "history"
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:  # Exit
        b4_pressed = True
        button_selection = "normal"
        lcd.write(0x01, light=0x00)


def handle_temp_legend():
    global b1_pressed, clear_LCD, button_selection

    if b1.value() == 0 and not b1_pressed:
        b1_pressed = True
        display.main_temps(temp_units, high_temps, low_temps)
        clear_LCD = time.ticks_ms()
        button_selection = "temperatures"


def handle_history():
    global clear_LCD, screen_timeout, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global current_viewing_day

    if b1.value() == 0 and not b1_pressed:  # Back
        b1_pressed = True
        current_viewing_day -= 1
        if current_viewing_day < -len(history_records):
            current_viewing_day += 1
        display.history(
            history_records[current_viewing_day],
            current_viewing_day,
            temp_units,
        )
        clear_LCD = time.ticks_ms()

    if b2.value() == 0 and not b2_pressed:  # Forward
        b2_pressed = True
        current_viewing_day += 1
        if current_viewing_day >= 0:
            current_viewing_day = -1
        display.history(
            history_records[current_viewing_day],
            current_viewing_day,
            temp_units,
        )
        clear_LCD = time.ticks_ms()

    if b3.value() == 0 and not b3_pressed:  # Back to temp screen
        b3_pressed = True
        display.main_temps(temp_units, high_temps, low_temps)
        clear_LCD = time.ticks_ms()
        screen_timeout = 20000
        button_selection = "temperatures"

    if b4.value() == 0 and not b4_pressed:  # Exit
        b4_pressed = True
        button_selection = "normal"
        lcd.write(0x01, light=0x00)


def handle_passcode():
    global clear_LCD, screen_timeout, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global passcode

    if b1.value() == 0 and not b1_pressed:
        b1_pressed = True
        passcode.append(1)
        display.passcode_asterisk(passcode)

    if b2.value() == 0 and not b2_pressed:
        b2_pressed = True
        passcode.append(2)
        display.passcode_asterisk(passcode)

    if b3.value() == 0 and not b3_pressed:
        b3_pressed = True
        passcode.append(3)
        display.passcode_asterisk(passcode)

    if b4.value() == 0 and not b4_pressed:
        b4_pressed = True
        passcode.append(4)
        display.passcode_asterisk(passcode)

    if len(passcode) >= 6:
        if passcode == secret_settings_passcode:
            clear_LCD = time.ticks_ms()
            screen_timeout = 20000
            lcd.write(0x01)

            if door_reset:
                lcd.print_text("doorReset", 0, 0)
            else:
                lcd.print_text("DoorOFF  ", 0, 0)
            if sensor_switch.value() == 0:
                lcd.print_text("Sensors ON", 0, 10)
            else:
                lcd.print_text("Sensors OFF", 0, 9)
            lcd.print_text("1 - LED & Sensors ON", 2, 0)
            lcd.print_text("4 - Exit", 3, 6)
            button_selection = "secretSettingsMenu"

        elif passcode == settings_passcode:
            clear_LCD = time.ticks_ms()
            screen_timeout = 20000
            lcd.write(0x01)

            lcd.print_text("1 - Change Temp Units", 1, 0)
            lcd.print_text("2 - Set Time", 2, 0)
            lcd.print_text("4 - Exit", 3, 6)
            button_selection = "settingsMenu"

        else:
            passcode = []
            clear_LCD = time.ticks_ms()
            lcd.print_text("Incorrect   ", 2, 5)


def handle_secret_settings_menu():
    global clear_LCD, button_selection
    global b1_pressed, b4_pressed
    global led_main, door_reset

    if b1.value() == 0 and not b1_pressed:
        b1_pressed = True
        led_main = True
        door_reset = True
        sensor_switch.value(0)  # Sensor ON
        sleep(0.5)
        lcd.init()
        bot_led.value(1)
        top_led.value(1)
        mid_led.value(1)
        sleep(0.1)
        lcd.print_text("Door Reset Sensor ON", 0, 0)
        lcd.print_text("1 - LED & Sensors ON", 2, 0)
        lcd.print_text("4 - Exit", 3, 6)
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:
        b4_pressed = True
        button_selection = "normal"
        lcd.write(0x01, light=0x00)


def handle_settings_menu():
    global clear_LCD, button_selection
    global b1_pressed, b2_pressed, b4_pressed
    global current_time_selection, hour_selection, minute_selection

    if b1.value() == 0 and not b1_pressed:
        b1_pressed = True
        clear_LCD = time.ticks_ms()
        button_selection = "setTempUnits"
        display.set_temp_units(temp_units)

    if b2.value() == 0 and not b2_pressed:
        b2_pressed = True
        clear_LCD = time.ticks_ms()
        button_selection = "setTime"
        current_time_selection = 0  # 0 = 'h', 1 = 'min'
        t = time.localtime()
        hour_selection = t[3]
        minute_selection = t[4]
        display.set_time(
            hour_input=hour_selection,
            minute_input=minute_selection,
        )

    if b4.value() == 0 and not b4_pressed:
        b4_pressed = True
        button_selection = "normal"
        lcd.write(0x01, light=0x00)


def handle_set_temp_units():
    global clear_LCD, button_selection
    global b1_pressed, b3_pressed, b4_pressed
    global temp_units

    if b1.value() == 0 and not b1_pressed:
        b1_pressed = True
        clear_LCD = time.ticks_ms()
        temp_units = "f" if temp_units == "c" else "c"
        display.set_temp_units(temp_units)

    if b3.value() == 0 and not b3_pressed:
        b3_pressed = True
        clear_LCD = time.ticks_ms()
        lcd.write(0x01)
        lcd.print_text("1 - Change Temp C/F", 1, 0)
        lcd.print_text("2 - Set Time", 2, 0)
        lcd.print_text("4 - Exit", 3, 6)
        button_selection = "settingsMenu"

    if b4.value() == 0 and not b4_pressed:
        b4_pressed = True
        clear_LCD = time.ticks_ms()
        lcd.write(0x01)
        lcd.print_text("1 - Change Temp C/F", 1, 0)
        lcd.print_text("2 - Set Time", 2, 0)
        lcd.print_text("4 - Exit", 3, 6)
        button_selection = "settingsMenu"


def handle_set_time():
    global clear_LCD, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global current_time_selection, hour_selection, minute_selection
    global saved_humidity

    if b1.value() == 0 and not b1_pressed:  # Up settings
        b1_pressed = True
        if current_time_selection == 0:
            hour_selection -= 1
        if current_time_selection == 1:
            minute_selection -= 1
        if hour_selection < 0: hour_selection = 23
        if minute_selection < 0: minute_selection = 59
        if current_time_selection != 2:
            display.set_time(
                hour_input=hour_selection,
                minute_input=minute_selection,
                selected=current_time_selection,
            )
        else:
            t_tuple = (2020, 1, 1, 2, hour_selection, minute_selection, 0, 0)
            RTC().datetime(t_tuple)
            saved_humidity = [0] * 24
            lcd.write(0x01)
            lcd.print_text("1 - Change Temp C/F", 1, 0)
            lcd.print_text("2 - Set Time", 2, 0)
            lcd.print_text("4 - Exit", 3, 6)
            button_selection = "settingsMenu"
        clear_LCD = time.ticks_ms()

    if b2.value() == 0 and not b2_pressed:  # Down settings
        b2_pressed = True
        if current_time_selection == 0:
            hour_selection += 1
        if current_time_selection == 1:
            minute_selection += 1
        if hour_selection > 23: hour_selection = 0
        if minute_selection > 59: minute_selection = 0
        if current_time_selection != 2:
            display.set_time(
                hour_input=hour_selection,
                minute_input=minute_selection,
                selected=current_time_selection,
            )
        else:
            t_tuple = (2020, 1, 1, 2, hour_selection, minute_selection, 0, 0)
            RTC().datetime(t_tuple)
            saved_humidity = [0] * 24
            lcd.write(0x01)
            lcd.print_text("1 - Change Temp C/F", 1, 0)
            lcd.print_text("2 - Set Time", 2, 0)
            lcd.print_text("4 - Exit", 3, 6)
            button_selection = "settingsMenu"
        clear_LCD = time.ticks_ms()

    if b3.value() == 0 and not b3_pressed:  # Next Option
        b3_pressed = True
        current_time_selection += 1
        if current_time_selection >= 3:
            current_time_selection = 0
        display.set_time(
            hour_input=hour_selection,
            minute_input=minute_selection,
            selected=current_time_selection,
        )
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:  # Exit without saving
        b4_pressed = True
        clear_LCD = time.ticks_ms()
        lcd.write(0x01)
        lcd.print_text("1 - Change Temp C/F", 1, 0)
        lcd.print_text("2 - Set Time", 2, 0)
        lcd.print_text("4 - Exit", 3, 6)
        button_selection = "settingsMenu"


def handle_humidity():
    global clear_LCD, button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global humidity_state_temp, humidity_shut_off_temp
    global current_humidity_selection, hum_selected_hour, hum_hours_ago

    if b1.value() == 0 and not b1_pressed:  # Enter settings
        b1_pressed = True
        display.humidity_settings(humidity_state, humidity_off_percent)
        humidity_state_temp, humidity_shut_off_temp = (
            humidity_state,
            humidity_off_percent,
        )
        current_humidity_selection = 0
        clear_LCD = time.ticks_ms()
        button_selection = "humiditySettings"

    if b2.value() == 0 and not b2_pressed:  # Humidity Records
        b2_pressed = True
        hum_hours_ago = 0
        hum_selected_hour = time.localtime()[3]
        display.humidity_records(
            min_hum,
            max_hum,
            saved_humidity,
            hum_selected_hour,
        )
        clear_LCD = time.ticks_ms()
        button_selection = "humidityRecords"

    if b3.value() == 0 and not b3_pressed:  # Refresh Display
        b3_pressed = True
        display.humidity(
            humidity_sensor_1,
            humidity_sensor_2,
            humidity_state,
            humidity_off_percent,
            temp_units,
        )
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:  # Exit
        b4_pressed = True
        button_selection = "normal"
        lcd.write(0x01, light=0x00)


def handle_humidity_records():
    global clear_LCD, button_selection
    global b1_pressed, b2_pressed, b4_pressed
    global hum_selected_hour, hum_hours_ago

    if b1.value() == 0 and not b1_pressed:  # Forward in time
        b1_pressed = True 
        hum_hours_ago = max(0, hum_hours_ago - 6)
        hum_selected_hour = (time.localtime()[3] - hum_hours_ago) % 24
        display.humidity_records(
            min_hum,
            max_hum,
            saved_humidity,
            hum_selected_hour,
        )
        clear_LCD = time.ticks_ms()

    if b2.value() == 0 and not b2_pressed:  # Backward in time
        b2_pressed = True
        hum_hours_ago = min(18, hum_hours_ago + 6)
        hum_selected_hour = (time.localtime()[3] - hum_hours_ago) % 24
        display.humidity_records(
            min_hum,
            max_hum,
            saved_humidity,
            hum_selected_hour,
        )
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:  # Return
        b4_pressed = True
        display.humidity(
            humidity_sensor_1,
            humidity_sensor_2,
            humidity_state,
            humidity_off_percent,
            temp_units,
        )
        clear_LCD = time.ticks_ms()
        button_selection = "humidity"


def handle_humidity_settings():
    global clear_LCD , button_selection
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed
    global humidity_state_temp, humidity_shut_off_temp
    global current_humidity_selection, humidity_state, humidity_off_percent

    if b1.value() == 0 and not b1_pressed:  # Down settings
        b1_pressed = True
        if current_humidity_selection == 0:
            humidity_state_temp -= 1
        if current_humidity_selection == 1:
            humidity_shut_off_temp -= 1
        humidity_state_temp = max(humidity_state_temp, 0)
        humidity_shut_off_temp = max(humidity_shut_off_temp, 0)
        if current_humidity_selection != 2:
            display.humidity_settings(
                humidity_state_temp,
                humidity_shut_off_temp,
                current_humidity_selection,
            )
        else:
            humidity_state, humidity_off_percent = (
                humidity_state_temp,
                humidity_shut_off_temp,
            )
            display.humidity(
                humidity_sensor_1,
                humidity_sensor_2,
                humidity_state,
                humidity_off_percent,
                temp_units,
            )
            button_selection = "humidity"
        clear_LCD = time.ticks_ms()

    if b2.value() == 0 and not b2_pressed:  # Up settings
        b2_pressed = True
        if current_humidity_selection == 0:
            humidity_state_temp += 1
        if current_humidity_selection == 1:
            humidity_shut_off_temp += 1
        humidity_state_temp = min(humidity_state_temp, 2)
        humidity_shut_off_temp = min(humidity_shut_off_temp, 100)
        if current_humidity_selection != 2:
            display.humidity_settings(
                humidity_state_temp,
                humidity_shut_off_temp,
                current_humidity_selection,
            )
        else:
            humidity_state, humidity_off_percent = (
                humidity_state_temp,
                humidity_shut_off_temp,
            )
            display.humidity(
                humidity_sensor_1,
                humidity_sensor_2,
                humidity_state,
                humidity_off_percent,
                temp_units,
            )
            button_selection = "humidity"
        clear_LCD = time.ticks_ms()

    if b3.value() == 0 and not b3_pressed:  # Next Option
        b3_pressed = True
        current_humidity_selection += 1
        if current_humidity_selection >= 3:
            current_humidity_selection = 0
        display.humidity_settings(
            humidity_state_temp,
            humidity_shut_off_temp,
            current_humidity_selection,
        )
        clear_LCD = time.ticks_ms()

    if b4.value() == 0 and not b4_pressed:  # Exit without saving
        b4_pressed = True
        display.humidity(
            humidity_sensor_1,
            humidity_sensor_2,
            humidity_state,
            humidity_off_percent,
            temp_units,
        )
        clear_LCD = time.ticks_ms()
        button_selection = "humidity"


def handle_release_buttons():
    global b1_pressed, b2_pressed, b3_pressed, b4_pressed

    if b1.value() == 1:
        b1_pressed = False
    if b2.value() == 1:
        b2_pressed = False
    if b3.value() == 1:
        b3_pressed = False
    if b4.value() == 1:
        b4_pressed = False


def handle_screen_timeout():
    global screen_timeout, screen_on, button_selection

    time_diff = time.ticks_diff(time.ticks_ms(), clear_LCD)
    if time_diff > screen_timeout and screen_on:
        screen_on = False
        button_selection = "normal"
        screen_timeout = 1000
        lcd.write(0x01, light=0x00)


def handle_humidity_update():
    global checked_humidity, max_hum, min_hum, set_saved_humidity, mean_hum

    # Checked every minute
    if second == 0 and not checked_humidity:
        checked_humidity = True
        
        humidity_data = sensors.read_humidity(hum_sensor_list)
        
        if humidity_data is  None:
            checked_humidity = False
            time.sleep(0.2)
            return
        
        hum_1 = humidity_data[0][1]
        hum_2 = humidity_data[1][1]
        mean_hum = (hum_1 + hum_2) / 2

        # humidityONOFF.value(1) == OFF plug
        # ["AUTO", "ON", "OFF"] -> 0, 1, 2

        if humidity_state == 2:
            humidity_switch.value(1)
        elif humidity_state == 1:
            humidity_switch.value(0)
        else:
            if mean_hum >= humidity_off_percent:
                humidity_switch.value(1)
            elif mean_hum <= (humidity_off_percent - 2):
                humidity_switch.value(0)

        max_hum = max(max_hum, max(hum_1, hum_2))
        min_hum = min(min_hum, min(hum_1, hum_2))

    elif second != 0:
        checked_humidity = False

    # Checked every hour, at the beginning of the hour
    if minute == 5 and second == 0 and not set_saved_humidity:
        set_saved_humidity = True
        saved_humidity[hour] = mean_hum

    elif second != 0:
        set_saved_humidity = False


def handle_door_button():
    global door_reset_btn_pressed, door_preset_time
    global door_preset_used, door_reset

    # Reset Button Clicked
    if door_reset_button.value() == 0 and not door_reset_btn_pressed:
        door_reset_btn_pressed = True
        if not door_open and led_main and sensor_switch.value() == 0:
            if door_reset:  # Preset 30 minutes
                door_preset_time = time.ticks_ms()
                door_preset_used = False
                mid_led.value(1)
                sleep(0.1)
                mid_led.value(0)
            else:
                # Reset LED after Preset
                time_diff = time.ticks_diff(time.ticks_ms(), door_preset_time)
                if time_diff < 1000 * 60 * 30 and not door_preset_used:
                    door_reset = True
                    door_preset_used = True
                    top_led.value(1)
                    sleep(0.1)
                    top_led.value(0)

    if door_reset_button.value() == 1:
        door_reset_btn_pressed = False


def handle_motion_detection_and_alert():
    global bot_sens_prev, top_sens_prev, mid_sens_prev, door_open, door_reset

    if not door_open and door_reset and led_main:  # Relay of Sensor to LEDs
        if bot_motion_sens.value() == 1 and bot_sens_prev == 0:
            bot_sens_prev = 1
            for i in range(2):  # Rapid Blink
                bot_led.value(1)
                sleep(0.03)
                bot_led.value(0)
                sleep(0.03)
        elif bot_motion_sens.value() == 1:
            bot_led.value(1)
        elif bot_motion_sens.value() == 0:
            bot_led.value(0)
            bot_sens_prev = 0

        if top_motion_sens.value() == 1 and top_sens_prev == 0:
            top_sens_prev = 1
            for i in range(2):  # Rapid Blink
                top_led.value(1)
                sleep(0.03)
                top_led.value(0)
                sleep(0.03)
        elif top_motion_sens.value() == 1:
            top_led.value(1)
        elif top_motion_sens.value() == 0:
            top_led.value(0)
            top_sens_prev = 0

        if mid_motion_sens.value() == 1 and mid_sens_prev == 0:
            mid_sens_prev = 1
            for i in range(2):  # Rapid Blink
                mid_led.value(1)
                sleep(0.03)
                mid_led.value(0)
                sleep(0.03)
        elif mid_motion_sens.value() == 0:
            mid_led.value(0)
            mid_sens_prev = 0

    if door_button.value() == 0:  # Door Open
        bot_led.value(0)
        mid_led.value(0)
        top_led.value(0)
        door_open = True
        door_reset = False
    else:
        door_open = False


def midnight_reset():
    global clear_LCD, screen_timeout, button_selection, screen_on
    global high_temps, low_temps, reset_midnight_temps
    global max_hum, min_hum

    if hour == 0 and minute == 0 and second == 0:  # Midnight Reset
        was_screen_on = screen_on
        if was_screen_on:
            button_selection = "normal"
            clear_LCD = time.ticks_ms()
            screen_timeout = 2000
            lcd.write(0x01)
            lcd.print_text("Midnight Measure", 1, 2)
            lcd.print_text("DO NOT TOUCH", 2, 4)
            time.sleep(1)

        recordString = ""

        for i, v in enumerate(high_temps):
            recordString += f"{v:.1f} "
            recordString += f"{low_temps[i]:.1f} "

        history_records.append(recordString.rstrip())
        if len(history_records) > 7:
            history_records.pop(0)
        storage.save_history(history_records)

        temps = sensors.read_temperatures(show=False)
        if temps is not None:
            high_temps = list(temps)
            low_temps = list(temps)
            reset_midnight_temps = True
        else:
            reset_midnight_temps = False

        humidity_data = sensors.read_humidity(hum_sensor_list)
        if humidity_data is not None:
            hum_1 = humidity_data[0][1]
            hum_2 = humidity_data[1][1]
            max_hum = max(hum_1, hum_2)
            min_hum = min(hum_1, hum_2)
        else:
            max_hum = 0
            min_hum = 100
        
        if was_screen_on:
            screen_on = False
            lcd.write(0x01, light=0x00)
        sleep(0.2)

    elif minute % 10 == 0 and second == 0 and not screen_on:
        temps = sensors.read_temperatures(show=False)
        if temps is not None:
            if not reset_midnight_temps:
                high_temps = list(temps)
                low_temps = list(temps)
                reset_midnight_temps = True

            for i, v in enumerate(temps):
                high_temps[i] = max(high_temps[i], v)
                low_temps[i] = min(low_temps[i], v)

        sleep(0.2)

try:
    while True:
        if button_selection == "normal":
            handle_normal()
        elif button_selection == "temperatures":
            handle_temperatures()
        elif button_selection == "tempLegend":
            handle_temp_legend()
        elif button_selection == "history":
            handle_history()
        elif button_selection == "passcode":
            handle_passcode()
        elif button_selection == "secretSettingsMenu":
            handle_secret_settings_menu()
        elif button_selection == "settingsMenu":
            handle_settings_menu()
        elif button_selection == "setTempUnits":
            handle_set_temp_units()
        elif button_selection == "setTime":
            handle_set_time()
        elif button_selection == "humidity":
            handle_humidity()
        elif button_selection == "humiditySettings":
            handle_humidity_settings()
        elif button_selection == "humidityRecords":
            handle_humidity_records()

        handle_screen_timeout()

        handle_release_buttons()

        handle_door_button()

        t = time.localtime()
        hour = t[3]
        minute = t[4]
        second = t[5]

        handle_motion_detection_and_alert()

        handle_humidity_update()

        midnight_reset()

        sleep(0.01)
    
except Exception as e:
    with open("log.txt", "a") as f:
        f.write("Crash Occurred:")
        sys.print_exception(e, f)
    while True:
        # System becomes unresponsive to indicate fault
        time.sleep(1)
