from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError


def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    scanner = Scanner().withDelegate(ScanDelegate())
    try:
        get_scan_result = scanner.scan(float(timeout))
        return get_scan_result
    except BTLEManagementError:
        return
