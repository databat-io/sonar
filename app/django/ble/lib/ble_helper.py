from bluepy.btle import Scanner, DefaultDelegate


def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    scanner = Scanner().withDelegate(ScanDelegate())
    return scanner.scan(float(timeout))
