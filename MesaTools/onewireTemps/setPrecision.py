import time

from w1thermsensor import W1ThermSensor


def setAllSensors(precision=9):
    for sensor in W1ThermSensor.get_available_sensors():
        sty = sensor.type_name
        sid = sensor.id
        stp = sensor.get_temperature()
        print("Setting precision of sensor %s (%s) to %d" % 
              (sid, sty, precision))
        sensor.set_precision(precision, persist=True)
        time.sleep(3)


if __name__ == "__main__":
    """ 
    Be careful with this!  Don't do it in a loop, because the EEPROM
    that stores the desired precision has a limited amount of writes.

    This *probably* needs root permissions to succeed since it fiddles
    with stuff in /sys/bus/w1/...
    """
    # The precision can be set from 9 to 12 bits
    precision = 12
    setAllSensors(precision=precision)

