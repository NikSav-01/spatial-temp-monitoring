import lcd
import sensors


# Display Temps, Current, High/Low from 12 AM
def main_temps(units, high_temps, low_temps):
    if units == "f":
        temps = sensors.read_temperatures(unit="f")
    else:
        temps = sensors.read_temperatures()
    if temps != None:
        lcd.write(0x01)
        lcd.print_text("Frt|Bck|Hal|Rom|Ligt", 0)

        if units == "f":
            high_temps = [sensors.c_2_f(i) for i in high_temps]
            low_temps = [sensors.c_2_f(i) for i in low_temps]

        for i, temp in enumerate(temps):
            lcd.print_text(f"{temp * 10:.0f}", 1, (i) * 4)
            lcd.print_text(f"{high_temps[i] * 10:.0f}", 2, i * 4)
            lcd.print_text(f"{low_temps[i] * 10:.0f}", 3, i * 4)

    else:
        lcd.write(0x01)
        lcd.print_text("Error Reading Temp", 0)


def temp_legend():
    lcd.write(0x01)
    lcd.print_text("Order| No decimals", 0)
    lcd.print_text("Curr | / temps by 10", 1)
    lcd.print_text("High |H/L Data since", 2)
    lcd.print_text("Low  |since midnight", 3)


def history(info, days_back, units):
    temps_to_display = info.split(" ")
    temps_to_display = [float(i) for i in temps_to_display]
    if units == "f":
        temps_to_display = [sensors.c_2_f(i) for i in temps_to_display]
    temps_to_display = [int(i * 10) for i in temps_to_display]

    lcd.write(0x01)

    if days_back == -1:
        lcd.print_text(f"{abs(days_back)} Day Ago", 0, 4)
    else:
        lcd.print_text(f"{abs(days_back)} Days Ago", 0, 4)

    lcd.print_text("Frt|Bck|Hal|Rom|Ligt", 1)

    for i, v in enumerate(temps_to_display):
        lcd.print_text(f"{v}", (i % 2) + 2, (int(i / 2)) * 4)


def set_time(hour_input="00", minute_input="00", selected=0):
    hour_input, minute_input = str(hour_input), str(minute_input)
    if len(hour_input) != 2:
        hour_input = "0" + hour_input
    if len(minute_input) != 2:
        minute_input = "0" + minute_input
    lcd.write(0x01)
    lcd.print_text("Set Time", 0, 6)
    lcd.print_text("Save", 3, 16)
    lcd.print_text(f"{hour_input}:{minute_input}", 1, 7)
    if selected == 0:
        lcd.print_text("^", 2, 7)
        lcd.print_text("|", 3, 7)
    if selected == 1:
        lcd.print_text("^", 2, 10)
        lcd.print_text("|", 3, 10)
    if selected == 2:
        lcd.print_text("|", 1, 18)
        lcd.print_text("V", 2, 18)


def set_temp_units(units):
    lcd.write(0x01)
    lcd.print_text(f"Current Units: {units}", 1, 2)


def passcode_asterisk(code):
    if len(code) == 1:
        lcd.print_text("  " + "*" * len(code) + " " * 6, 2, 5)
    else:
        lcd.print_text("*" * len(code), 2, 7)


def humidity(sens_1, sens_2, state, off_percent, unit):
    lcd.write(0x01)
    
    humidity_data = sensors.read_humidity([sens_1, sens_2], unit)
    if humidity_data is not None:
        sens_1_hum = humidity_data[0]
        sens_2_hum = humidity_data[1]
    else:
        lcd.print_text("Error Reading", 0, 3)
        lcd.print_text("Sensors", 1, 6)
        return

    humidity_options = ["AUTO", "ON", "OFF"]
    h = humidity_options[state]

    lcd.print_text("Light Door  |Status", 0, 1)
    lcd.print_text(f"|{' ' * int(3 - (len(h) / 2))}{h}", 1, 13)
    lcd.print_text("|OFF AT", 2, 13)
    lcd.print_text(f"| {off_percent} %", 3, 13)
    lcd.print_text(f"{sens_1_hum[0]:.2f}", 1, 1)
    lcd.print_text(f"{sens_2_hum[0]:.2f}", 1, 7)
    lcd.print_text(f"{sens_1_hum[1]}%", 2, 1)
    lcd.print_text(f"{sens_2_hum[1]}%", 2, 7)


def humidity_settings(state, off_percent, selector=0):
    humidity_options = ["AUTO", "ON", "OFF"]
    lcd.write(0x01)
    lcd.print_text(f"Status: {humidity_options[state]}", 0)
    lcd.print_text(f"Max humidity: {off_percent}%", 1)
    lcd.print_text("Save", 3, 16)
    if selector == 0:
        lcd.print_text("<-", 0, 18)
    elif selector == 1:
        lcd.print_text("<-", 1, 18)
    else:
        lcd.print_text("->", 3, 13)


def humidity_records(min_h, max_h, records, hour):
    lcd.write(0x01)
    lcd.print_text(f"H: {max_h}% | L: {min_h}%", 0)
    s = hour - 5
    if s > 0:
        for i, v in enumerate(records[s : hour + 1]):
            line = 3 - (i // 2)
            line_offset = 10 * (1 - i % 2)
            lcd.print_text(f"{s + i}: {v}%", line, line_offset)
    else: 
        for i, v in enumerate(records[hour - 5:] + records[:hour + 1]):
            line = 3 - (i // 2)
            line_offset = 10 * (1 - i % 2)
            lcd.print_text(f"{(s + i) % 24}: {v}%", line, line_offset)
