import time, ds18x20, onewire, ubinascii
from machine import SoftI2C, Pin, RTC
from time import sleep

# I2C Setup
i2c = SoftI2C(scl=Pin(1), sda=Pin(0), freq=100_000)
LCD_ADDR = 39

# LCD Command Helper
def lcd_write(cmd, rs=0, light=0x00):
    high_nibble = (cmd & 0xF0) | (rs << 0) | 0x04 | light # RS=0 for cmd, RS=1 for data
    low_nibble = ((cmd << 4) & 0xF0) | (rs << 0) | 0x04 | light
    i2c.writeto(LCD_ADDR, bytes([high_nibble, high_nibble & 0xFB, low_nibble, low_nibble & 0xFB]))
    sleep(0.001)  # Delay between commands

def lcd_init():
    lcd_write(0x33)  # Initialize
    sleep(0.01)      
    lcd_write(0x32)  # 4-bit mode
    sleep(0.005)
    lcd_write(0x28)  # 2 lines, 5x8 font
    sleep(0.001)
    lcd_write(0x0C)  # Display ON, backlight ON
    lcd_write(0x01)  # Clear screen
    sleep(0.2)       

def lcd_print(text, line=0, col=0,light=0x00):
    line_offsets = [0x00, 0x40, 0x14, 0x54]
    lcd_write(0x80 | (line_offsets[line] + col))  # Set cursor
    for char in text:
        lcd_write(ord(char), rs=1,light=light)  # Write char

lcd_init()

settingsPasscode = []
decoySettingsPasscode = []
try:
    with open('secret.txt', 'r') as f:
        file = f.readlines()
        for i in file[0].strip().split(','):
            settingsPasscode.append(int(i))
        for i in file[1].strip().split(','):
            decoySettingsPasscode.append(int(i))
except:
    # Created secret.txt, but passwords are default
    with open('secret.txt', 'w') as f:
        with open('secret1.txt', 'w') as f:
            f.write("1, 1, 1, 1, 1, 1\n2, 2, 2, 2, 2, 2")
    settingsPasscode = [1, 1, 1, 1, 1, 1]
    decoySettingsPasscode = [2, 2, 2, 2, 2, 2]

ow_pin = Pin(13, Pin.PULL_UP)
ow = onewire.OneWire(ow_pin)
ds = ds18x20.DS18X20(ow)
roms = ds.scan() 

def read_temperatures(ds, roms, show=True, MM=False):
    try:
        ds.convert_temp()
        if not show and MM: lcd_print("MEASURING", 1, 5, light=0x08)
        if show:
            lcd_write(0x01, light=0x08)
            lcd_print("MEASURING", 1, 5, light=0x08)
        time.sleep_ms(1000)  # Wait for conversion
        temps = {}
        for rom in roms:
            rom_str = ubinascii.hexlify(rom).decode()  # Convert bytearray to string
            temps[rom_str] = ds.read_temp(rom)
        return temps
    except:
        return None

Days = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')

def get_time(part,goBack=0): # goBack in seconds
    Ctime = time.localtime(time.mktime(time.localtime()) - goBack)
    times = []
    for i in part:
        if i == 'y':     # Year
            times.append(Ctime[0])
        elif i == 'mon': # Month
            times.append(Ctime[1])
        elif i == 'd':   # Day
            times.append(Ctime[2])
        elif i == 'h':   # Hour
            times.append(Ctime[3])
        elif i == 'min': # Minute
            times.append(Ctime[4])
        elif i == 's':   # Second
            times.append(Ctime[5])
        elif i == 'wd':  # Weekday (0=Monday)
            times.append(Ctime[6])
    return times

def DisplayMainTemps(light=False): #Display Temps, Current, High/Low from 12 AM
    temps = read_temperatures(ds, roms)
    if temps != None:
        frontTemp = temps["287c485500000075"]
        backTemp = temps["28e3af52000000ed"]
        hallTemp = temps["287987be0000000e"]
        roomTemp = temps["2852ff51000000c0"]
        lightTemp = temps["28016abe00000001"]
        
        lcd_write(0x01, light=0x08)
        lcd_print(f"Front {frontTemp:.1f} {frontTempHigh:.1f} {frontTempLow:.1f}", 0, light=0x08)
        lcd_print(f"Back  {backTemp:.1f} {backTempHigh:.1f} {backTempLow:.1f}", 1, light=0x08)
        lcd_print(f"Hall  {hallTemp:.1f} {hallTempHigh:.1f} {hallTempLow:.1f}", 2, light=0x08)
        lcd_print(f"Room  {roomTemp:.1f} {roomTempHigh:.1f} {roomTempLow:.1f}", 3, light=0x08)
    
        if light: return frontTemp, lightTemp
    
    else:
        lcd_write(0x01, light=0x08)
        lcd_print("Error Reading Temp", 0, ad1, light=0x08)

def DisplayPasscodeAsterisk(code):
    if len(code) == 1: lcd_print("  "+"*"*len(code)+" "*6, 2, 5, light=0x08)
    else: lcd_print("*"*len(code), 2, 7, light=0x08)

def DisplayHistory(info):
    day, date, frontH, frontL, backH, backL, hallH, hallL, roomH, roomL, lightH, lightL = info.split(" ")
    lcd_write(0x01, light=0x08)
    lcd_print(f"{day} {date}  | F {frontH} {frontL}", 0, light=0x08)
    lcd_print(f"_______| B {backH} {backL}", 1, light=0x08)
    lcd_print(f"L {lightH} | H {hallH} {hallL}", 2, light=0x08)
    lcd_print(f"  {lightL} | R {roomH} {roomL}", 3, light=0x08)
    
def SaveHistoryToText(toSave):
    with open('history.txt', 'w') as f:
        for line in toSave:
            for i in line:
                f.write(str(i) + " ")
            f.write('\n')

def ExtractHistoryFromText():
    records = []
    try:
        with open('history.txt', 'r') as f:
            for line in f:
                records.append(line.strip())
        return records
    except: return records

def DisplaySetTime(yearInput='0000', monthInput='00', dayInput='00', hourInput='00', minuteInput='00', secondInput='00', weekdayInput='Mon', UpdateTime = False, Init = False, Save = False):
    year, month, day, hour, minute, second = get_time(['y','mon','d','h','min','s'])
    year, month, day, hour, minute, second = str(year), str(month), str(day), str(hour), str(minute), str(second)
    if len(month) != 2: month = "0" + month
    if len(day) != 2: day = "0" + day
    if len(hour) != 2: hour = "0" + hour
    if len(minute) != 2: minute = "0" + minute
    if len(second) != 2: second = "0" + second
    yearInput, monthInput, dayInput, hourInput, minuteInput, secondInput = str(yearInput), str(monthInput), str(dayInput), str(hourInput), str(minuteInput), str(secondInput)
    if len(monthInput) != 2: monthInput = "0" + monthInput
    if len(dayInput) != 2: dayInput = "0" + dayInput
    if len(hourInput) != 2: hourInput = "0" + hourInput
    if len(minuteInput) != 2: minuteInput = "0" + minuteInput
    if len(secondInput) != 2: secondInput = "0" + secondInput
    if Init:
        yearInput, monthInput, dayInput, hourInput, minuteInput, secondInput = year, month, day, hour, minute, second
    if UpdateTime:
        lcd_print(f"{year} {month} {day} {hour} {minute} {second}", 1, light=0x08)
    else:
        lcd_print("year mo da ho mi se", 0, light=0x08)
        lcd_print(f"{year} {month} {day} {hour} {minute} {second}", 1, light=0x08)
        lcd_print(f"{yearInput} {monthInput} {dayInput} {hourInput} {minuteInput} {secondInput}", 2, light=0x08)
        lcd_print(f"{weekdayInput}", 3, light=0x08)
        if Save: lcd_print("Save", 3, 16, light=0x08)
        else: lcd_print("Quit", 3, 16, light=0x08)

b1 = Pin(2, Pin.IN, Pin.PULL_UP)
b2 = Pin(3, Pin.IN, Pin.PULL_UP)
b3 = Pin(4, Pin.IN, Pin.PULL_UP)
b4 = Pin(5, Pin.IN, Pin.PULL_UP)
b1P,b2P,b3P,b4P = False,False,False,False

temps = read_temperatures(ds, roms)
print(temps)
if temps != None:
    frontTempHigh = frontTempLow = temps["287c485500000075"]
    backTempHigh = backTempLow = temps["28e3af52000000ed"]
    hallTempHigh = hallTempLow = temps["287987be0000000e"]
    roomTempHigh = roomTempLow = temps["2852ff51000000c0"]
    lightTempHigh = lightTempLow = temps["28016abe00000001"]
else:
    lcd_write(0x01, light=0x08)
    lcd_print("Error Reading Temp", 0, 1, light=0x08)
    lcd_print("Initial Reading", 1, 2, light=0x08)

clear_LCD = time.ticks_ms()
screenTimeout = 1000
screenOn = True

passcode = []
ButtonSelection = "normal"

BSens = Pin(6, Pin.IN, Pin.PULL_DOWN)
MSens = Pin(7, Pin.IN, Pin.PULL_DOWN)
TSens = Pin(8, Pin.IN, Pin.PULL_DOWN)

BLED = Pin(10, Pin.OUT) #RED
MLED = Pin(12, Pin.OUT) #BLUE
TLED = Pin(11, Pin.OUT) #YELLOW

BSensPrev = MSensPrev = TSensPrev = 0

SensorONOFF = Pin(14, Pin.OUT) #SensorOn.value() == 0, Sensors on

DoorButton = Pin(9, Pin.IN, Pin.PULL_UP)
DoorOpen = True #DoorButton.value() == 0, Open Door
DoorPresetTime = time.ticks_ms()

DoorResetButton = Pin(16, Pin.IN, Pin.PULL_UP)
DRBP = False
DoorReset = False
DoorResetPressTime = time.ticks_ms()
DoorPresetUsed = True

LEDMain = False

HistoryRecords = []
LoadHistoryRecords = ExtractHistoryFromText()
for i in LoadHistoryRecords:
    tempRecordList = []
    for j in i.split(" "):
        tempRecordList.append(j)
    HistoryRecords.append(tempRecordList)

ResetMidnightTemps = True

# TODO:
# Add a back up Try: Except: that if the main program fails, it runs the secondary program, LEDs and Sensors only. If this one fails as well, make sure to send a final command of turn off all LEDS
 
while True:
    if ButtonSelection == "normal":
        if b1.value() == 0 and not b1P: # LEDs & Sensor OFF
            b1P = True
            LEDMain = False
            DoorReset = False
            SensorONOFF.value(1) #Sensor OFF
             
        if b2.value() == 0 and not b2P:
            b2P = True
            frontTemp, lightTemp = DisplayMainTemps(light=True)
            currentTempFL = "Front"
            clear_LCD = time.ticks_ms()
            screenTimeout = 8000
            screenOn = True
            ButtonSelection = "temperatures"
            
        if b3.value() == 0 and not b3P: # History
            b3P = True
            #Add inital screen
            Records = ExtractHistoryFromText()
            if Records == []: #No Records
                lcd_write(0x01, light=0x08)
                lcd_print("No Records Yet", 0, 3, light=0x08)
                clear_LCD = time.ticks_ms()
                screenTimeout = 2000
                screenOn = True
            else:
                CurrentViewingDay = -1
                DisplayHistory(Records[CurrentViewingDay])
                clear_LCD = time.ticks_ms()
                screenTimeout = 8000
                screenOn = True
            ButtonSelection = "history"
         
        if b4.value() == 0 and not b4P: # Settings
            b4P = True
            passcode = []
            lcd_write(0x01, light=0x08)
            lcd_print("Settings", 0, 6, light=0x08)
            lcd_print("Password:", 1, 6, light=0x08)
            clear_LCD = time.ticks_ms()
            screenTimeout = 6000
            screenOn = True
            ButtonSelection = "passcode"
    
    if ButtonSelection == "history":
        if b1.value() == 0 and not b1P: # Back
            b1P = True
            CurrentViewingDay -= 1
            if CurrentViewingDay < -len(Records): CurrentViewingDay += 1
            DisplayHistory(Records[CurrentViewingDay])
            clear_LCD = time.ticks_ms()
        
        if b2.value() == 0 and not b2P: # Forward
            b2P = True
            CurrentViewingDay += 1
            if CurrentViewingDay == 0: CurrentViewingDay = -1
            DisplayHistory(Records[CurrentViewingDay])
            clear_LCD = time.ticks_ms()
            
        if b3.value() == 0 and not b3P:
            b3P = True
            lcd_init()
            ButtonSelection = "normal"

        if b4.value() == 0 and not b4P: # Escape
            b4P = True
            ButtonSelection = "normal"
            lcd_write(0x01)
    
    if ButtonSelection == "temperatures":
        if b1.value() == 0 and not b1P: # Legend for Temperature Screen
            b1P = True
            lcd_write(0x01, light=0x08)
            lcd_print(" Current  High  Low", 0, light=0x08)
            lcd_print("High/Low data", 2, 3, light=0x08)
            lcd_print("since midnight", 3, 3, light=0x08)
            
            clear_LCD = time.ticks_ms()
            ButtonSelection = "tempLegend"
            
        if b2.value() == 0 and not b2P: #Reset Timer for Temp Screen
            b2P = True
            clear_LCD = time.ticks_ms()
        
        if b3.value() == 0 and not b3P:
            b3P = True
            if currentTempFL == "Front":
                lcd_print(f"Light {lightTemp:.1f} {lightTempHigh:.1f} {lightTempLow:.1f}", 0, light=0x08)
                currentTempFL = "Light"
            else:
                lcd_print(f"Front {frontTemp:.1f} {frontTempHigh:.1f} {frontTempLow:.1f}", 0, light=0x08)
                currentTempFL = "Front"
            clear_LCD = time.ticks_ms()
        
        if b4.value() == 0 and not b4P: #Go back to clear screen
            b4P = True
            ButtonSelection = "normal"
            lcd_write(0x01)

    if ButtonSelection == "tempLegend":
        if b1.value() == 0 and not b1P:
            b1P = True
            DisplayMainTemps()
            clear_LCD = time.ticks_ms()
            ButtonSelection = "temperatures"

    if ButtonSelection == "passcode":
        if b1.value() == 0 and not b1P:
            b1P = True
            passcode.append(1)
            DisplayPasscodeAsterisk(passcode)
        
        if b2.value() == 0 and not b2P:
            b2P = True
            passcode.append(2)
            DisplayPasscodeAsterisk(passcode)
        
        if b3.value() == 0 and not b3P:
            b3P = True
            passcode.append(3)
            DisplayPasscodeAsterisk(passcode)
        
        if b4.value() == 0 and not b4P:
            b4P = True
            passcode.append(4)
            DisplayPasscodeAsterisk(passcode)
        
        if len(passcode) >= 6:
            if passcode == settingsPasscode:
                clear_LCD = time.ticks_ms()
                screenTimeout = 20000
                lcd_write(0x01, light=0x08)
                
                if DoorReset: lcd_print("DoorReset", 0, 0, light=0x08)
                else: lcd_print("DoorOFF  ", 0, 0, light=0x08)
                if SensorONOFF.value() == 0: lcd_print("Sensors ON", 0, 10, light=0x08)
                else: lcd_print("Sensors OFF", 0, 9, light=0x08)
                lcd_print("1 - LED & Sensors ON", 2, 0, light=0x08)
                lcd_print("4 - Exit", 3, 6, light=0x08)
                ButtonSelection = "settingsMenu"
            elif passcode == decoySettingsPasscode:
                clear_LCD = time.ticks_ms()
                screenTimeout = 20000
                lcd_write(0x01, light=0x08)
                
                lcd_print("1 - Reset Temp", 1, 0, light=0x08)
                lcd_print("2 - Set Time", 2, 0, light=0x08)
                lcd_print("4 - Exit", 3, 6, light=0x08)
                ButtonSelection = "decoySettingsMenu"
            else:
                passcode = []
                clear_LCD = time.ticks_ms()
                lcd_print("Incorrect   ", 2, 5, light=0x08)

    if ButtonSelection == "settingsMenu":
        if b1.value() == 0 and not b1P:
            b1P = True
            LEDMain = True
            DoorReset = True
            SensorONOFF.value(0) #Sensor ON
            sleep(0.5)
            lcd_init()
            BLED.value(1)
            TLED.value(1)
            sleep(0.1)
            BLED.value(1)
            TLED.value(1)
            lcd_print("DoorReset Sensors ON", 0, 0, light=0x08)
            lcd_print("1 - LED & Sensors ON", 2, 0, light=0x08)
            lcd_print("4 - Exit", 3, 6, light=0x08)
        
        if b4.value() == 0 and not b4P:
            b4P = True
            ButtonSelection = "normal"
            lcd_write(0x01)
            
    if ButtonSelection == "decoySettingsMenu":
        if b1.value() == 0 and not b1P:
            b1P = True
            lcd_print("Temp Sensors Reset", 0, 0, light=0x08)
        
        if b2.value() == 0 and not b2P:
            b2P = True
            DisplaySetTime(Init = True)
            clear_LCD = time.ticks_ms()
            ButtonSelection = "setTime"
            currentTimeSelection = 0 # 0 = 'y', 1 = 'mon', 2 = 'd', 3 = 'h', 4 = 'min', 5 = 's'
            yearSelection, monthSelection, daySelection, hourSelection, minuteSelection, secondSelection, weekdaySelection = get_time(['y','mon','d','h','min','s','wd'])
            previousSecond = get_time(['s'])[0]
            SaveTimeSelection = False
        
        if b4.value() == 0 and not b4P:
            b4P = True
            ButtonSelection = "normal"
            lcd_write(0x01)

    
    if ButtonSelection == "setTime":
        currentSecond = get_time(['s'])[0]
        if currentSecond != previousSecond:
            DisplaySetTime(UpdateTime = True)
            previousSecond = currentSecond
            clear_LCD = time.ticks_ms()
            
        if b1.value() == 0 and not b1P:
            b1P = True 
            if currentTimeSelection == 0: yearSelection -= 1
            if currentTimeSelection == 1: monthSelection -= 1
            if currentTimeSelection == 2: daySelection -= 1
            if currentTimeSelection == 3: hourSelection -= 1
            if currentTimeSelection == 4: minuteSelection -= 1
            if currentTimeSelection == 5: secondSelection -= 1
            if currentTimeSelection == 6: weekdaySelection -= 1
            if currentTimeSelection == 7: SaveTimeSelection = False
            if weekdaySelection < 0: weekdaySelection = 0
            elif weekdaySelection > 6: weekdaySelection = 6
            weekday = Days[weekdaySelection]
            DisplaySetTime(yearInput=yearSelection, monthInput=monthSelection, dayInput=daySelection, hourInput=hourSelection, minuteInput=minuteSelection, secondInput=secondSelection, weekdayInput=weekday, Save=SaveTimeSelection)
            clear_LCD = time.ticks_ms()
            
        if b2.value() == 0 and not b2P:
            b2P = True
            if currentTimeSelection == 0: yearSelection += 1
            if currentTimeSelection == 1: monthSelection += 1
            if currentTimeSelection == 2: daySelection += 1
            if currentTimeSelection == 3: hourSelection += 1
            if currentTimeSelection == 4: minuteSelection += 1
            if currentTimeSelection == 5: secondSelection += 1
            if currentTimeSelection == 6: weekdaySelection += 1
            if currentTimeSelection == 7: SaveTimeSelection = True
            if weekdaySelection < 0: weekdaySelection = 0
            elif weekdaySelection > 6: weekdaySelection = 6
            weekday = Days[weekdaySelection]
            DisplaySetTime(yearInput=yearSelection, monthInput=monthSelection, dayInput=daySelection, hourInput=hourSelection, minuteInput=minuteSelection, secondInput=secondSelection, weekdayInput=weekday, Save=SaveTimeSelection)
            clear_LCD = time.ticks_ms()
            
        if b3.value() == 0 and not b3P:
            b3P = True
            currentTimeSelection += 1
            if currentTimeSelection == 8: currentTimeSelection = 0
            clear_LCD = time.ticks_ms()
            
        if b4.value() == 0 and not b4P:
            b4P = True
            if SaveTimeSelection:
                RTC().datetime((yearSelection, monthSelection, daySelection, weekdaySelection, hourSelection, minuteSelection, secondSelection, 0))
            # TODO: Also, save this to a .txt file, so that next time I won't have to click so much
            clear_LCD = time.ticks_ms()
            screenTimeout = 20000
            lcd_write(0x01, light=0x08)
            lcd_print("1 - Reset Temp", 1, 0, light=0x08)
            lcd_print("2 - Set Time", 2, 0, light=0x08)
            lcd_print("4 - Exit", 3, 6, light=0x08)
            ButtonSelection = "decoySettingsMenu"
        
        
    if ButtonSelection == "NEXT":
        if b1.value() == 0 and not b1P:
            b1P = True
        
        if b2.value() == 0 and not b2P:
            b2P = True
        
        if b3.value() == 0 and not b3P:
            b3P = True
        
        if b4.value() == 0 and not b4P:
            b4P = True
            
    if b1.value() == 1: b1P = False
    if b2.value() == 1: b2P = False
    if b3.value() == 1: b3P = False
    if b4.value() == 1: b4P = False       
        
    if time.ticks_diff(time.ticks_ms(), clear_LCD) > screenTimeout and screenOn:
        screenOn = False
        ButtonSelection = "normal"
        screenTimeout = 1000
        lcd_write(0x01)
    
    #Track Temp High/Low
    hour, minute, second = get_time(['h','min','s'])
    if hour == 0 and minute == 0 and second == 0: #Midnight Reset
        if screenOn:
            ButtonSelection = "normal"
            clear_LCD = time.ticks_ms()
            screenTimeout = 2000
            lcd_write(0x01, light=0x08)
            lcd_print("Midnight Measure", 2, 2, light=0x08)
            time.sleep(1)
        
        dayNum, weekDay = get_time(['d','wd'],43200)
        actualDay = Days[weekDay]
        dayRecordTemps = (str(dayNum), actualDay, f"{frontTempHigh:.1f}", f"{frontTempHigh:.1f}", f"{backTempHigh:.1f}", f"{backTempLow:.1f}", f"{hallTempHigh:.1f}", f"{hallTempLow:.1f}", f"{roomTempHigh:.1f}", f"{roomTempLow:.1f}", f"{lightTempHigh:.1f}", f"{lightTempLow:.1f}")
        HistoryRecords.append(dayRecordTemps)
        if len(HistoryRecords) > 10: HistoryRecords.pop(0)
        SaveHistoryToText(HistoryRecords)
        
        temps = read_temperatures(ds, roms, show=False, MM=True)
        if temps != None:
            frontTempHigh = frontTempLow = temps["287c485500000075"]
            backTempHigh = backTempLow = temps["28e3af52000000ed"]
            hallTempHigh = hallTempLow = temps["287987be0000000e"]
            roomTempHigh = roomTempLow = temps["2852ff51000000c0"]
            lightTempHigh = lightTempLow = temps["28016abe00000001"]
            ResetMidnightTemps = True
        else:
            ResetMidnightTemps = False
            
        lcd_write(0x01)
        sleep(0.2)
    elif minute % 10 == 0 and second == 0 and not screenOn:
        temps = read_temperatures(ds, roms, show=False)
        if temps != None:
            if not ResetMidnightTemps:
                frontTempHigh = frontTempLow = temps["287c485500000075"]
                backTempHigh = backTempLow = temps["28e3af52000000ed"]
                hallTempHigh = hallTempLow = temps["287987be0000000e"]
                roomTempHigh = roomTempLow = temps["2852ff51000000c0"]
                lightTempHigh = lightTempLow = temps["28016abe00000001"]
                ResetMidnightTemps = True
            
            if temps["287c485500000075"] > frontTempHigh: frontTempHigh = temps["287c485500000075"]
            if temps["287c485500000075"] < frontTempLow: frontTempLow = temps["287c485500000075"]
            if temps["28e3af52000000ed"] > backTempHigh: backTempHigh = temps["28e3af52000000ed"]
            if temps["28e3af52000000ed"] < backTempLow: backTempLow = temps["28e3af52000000ed"]
            if temps["287987be0000000e"] > hallTempHigh: hallTempHigh = temps["287987be0000000e"]
            if temps["287987be0000000e"] < hallTempLow: hallTempLow = temps["287987be0000000e"]
            if temps["2852ff51000000c0"] > roomTempHigh: roomTempHigh = temps["2852ff51000000c0"]
            if temps["2852ff51000000c0"] < roomTempLow: roomTempLow = temps["2852ff51000000c0"]
            if temps["28016abe00000001"] > lightTempHigh: lightTempHigh = temps["28016abe00000001"]
            if temps["28016abe00000001"] < lightTempLow: lightTempLow = temps["28016abe00000001"]

        sleep(0.2)
    
    if not DoorOpen and DoorReset and LEDMain: #Relay of Sensor to LEDs
        if BSens.value() == 1 and BSensPrev == 0:
            BSensPrev = 1
            for i in range(5): #Rapid Blink 
                BLED.value(1)
                sleep(0.05)
                BLED.value(0)
                sleep(0.05)
        elif BSens.value() == 1:
            BLED.value(1)
        elif BSens.value() == 0:
            BLED.value(0)
            BSensPrev = 0

        if TSens.value() == 1 and TSensPrev == 0:
            TSensPrev = 1
            for i in range(5): #Rapid Blink 
                TLED.value(1)
                sleep(0.05)
                TLED.value(0)
                sleep(0.05)
        elif TSens.value() == 1:
            TLED.value(1)
        elif TSens.value() == 0:
            TLED.value(0)
            TSensPrev = 0
        
        if MSens.value() == 1 and MSensPrev == 0:
            MSensPrev = 1
            for i in range(5): #Rapid Blink 
                MLED.value(1)
                sleep(0.05)
                MLED.value(0)
                sleep(0.05)
        elif MSens.value() == 0:
            MLED.value(0)
            MSensPrev = 0
    
    if DoorButton.value() == 0: #Door Open
        BLED.value(0)
        MLED.value(0)
        TLED.value(0)
        DoorOpen = True
        DoorReset = False
    else:
        DoorOpen = False

    if DoorResetButton.value() == 0 and not DRBP: #Reset Button Clicked
        DRBP = True
        if not DoorOpen and LEDMain and SensorONOFF.value() == 0:
            if DoorReset: #Preset 30 minutes
                DoorPresetTime = time.ticks_ms()
                DoorPresetUsed = False
                MLED.value(1)
                sleep(0.1)
                MLED.value(0)
            else:
                if time.ticks_diff(time.ticks_ms(), DoorPresetTime) < 1000*60*30 and not DoorPresetUsed: # Reset LED after Preset
                    DoorReset = True
                    DoorPresetUsed = True
                    TLED.value(1)
                    sleep(0.1)
                    TLED.value(0)
    
    if DoorResetButton.value() == 1: DRBP = False
    
    sleep(0.01)