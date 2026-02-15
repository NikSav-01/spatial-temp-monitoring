# Spatial Detection and Thermal Monitoring

A stealth-focused environmental monitoring and presence detection system built on the Raspberry Pi Pico. This project integrates multi-zone microwave radar detection with movement alerts, a zero-visibility design to maintain operational secrecy during unauthorized entry, and thermal logging of ambient temperatures.


## System Architecture

### Presence Detection
The system utilizes 7x RCWL-0516 sensors to monitor three distinct zones through drywall, concealing all hardware from view.
- Zone 1 (Approach): 2 sensors at stairwell base. Triggers Red LED (5 rapid pulses (0.5s) + 1.5s solid dwell)
- Zone 2 (Proximity): 3 sensors spanning stairwell top. Triggers Blue LED (5 rapid pulses (0.5s))
- Zone 3 (Adjacent Room/Hallway): 2 sensors monitoring neighboring space. Triggers Yellow LED (5 rapid pulses (0.5s) + 1.5s solid dwell)

### Stealth & Security Logic
The core firmware handles complex logic to ensure the system remains undetected by anyone entering the room.
- Door Interrupt: A cabinet-style button monitors door state. If the door opens, all LED outputs are immediately killed, overriding any active sensor triggers, preventing detection.
- Grace Period Reset: A hidden button on top of the door allows a 30-minute window to exit/enter and rearm the system without UI interaction, given that the button is pressed *before* exiting the room.
- Dual-Password Authentication:
	- Standard Password: Allows reactivation of motion sensors and LEDs.
	- Decoy Password: Displays a fake "Settings" menu. This provides plausible deniability, hiding the existence of the monitoring system from unwanted parties.


### Thermal Monitoring
5x DS18B20 sensors provide thermal data display on an LCD screen:

- Exterior: Dual sensors on opposing gables to negate inaccuracies caused by direct sunlight.
- Interior: Hallway and dual room sensors.
- Logging: Maintains a 10-day rolling history accessible via the LCD interface.

### Hardware Integration

- Microcontroller: Raspberry Pi Pico
- Sensors: 7x RCWL-0516, 5x DS18B20, 1x Cabinet Button (Door State)
- Interface: 20x4 LCD (I2C), 5x Tactile Buttons
- Output: 3x Indicator LEDs, 1x Relay (Sensor Power Control)
- Implementation: Custom wiring with decoupling capacitors at remote sensor locations to ensure signal stability over extended distances.

### Repository Contents

|File|Description|
|-|-|
|main.py|Core MicroPython firmware, state machine logic, and UI handling.|
|history.txt.example|Mock data structure for 10-day thermal logging.|
|secret.txt.example|Mock structure for hardware authentication sequences.|

