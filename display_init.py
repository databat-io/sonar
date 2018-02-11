import os
import sys

try:
    import dot3k.backlight as backlight
    import dot3k.lcd as lcd
except:
    # Exit if we can't initialize the device.
    print('No LCD found.')
    sys.exit(1)

SSID = os.getenv('SSID', None)
SSID_PASSWORD = os.getenv('SSID_PASSWORD', None)
MODE = os.getenv('MODE')

lcd.clear()
lcd.set_contrast(50)
backlight.rgb(0, 0, 255)

if MODE == 'wifi':
    lcd.write('- WiFi Details -')
    lcd.write('SSID: {}'.format(SSID))
    lcd.write(' Pwd: {}'.format(SSID_PASSWORD))
else:
    lcd.clear()
    lcd.write('   Metricsor'.ljust(16))
    lcd.write('   device is'.ljust(16))
    lcd.write('  starting...'.ljust(16))
