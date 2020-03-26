# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on ?? ??? ????
#
#  @author: rhamilton

"""One line description of module.
Further description.
"""

from __future__ import division, print_function, absolute_import

import time

from w1thermsensor import W1ThermSensor

from ligmos import utils, workers


def readAllSensors():
    fields = {}
    for sensor in W1ThermSensor.get_available_sensors():
        sty = sensor.type_name
        sid = sensor.id
        stp = sensor.get_temperature()
        print("Sensor %s (%s) has temperature %.2f" % (sid, sty, stp))
        fields.update({sid: stp})

    pkt = utils.packetizer.makeInfluxPacket(meas=['temperatures'],
                                            fields=fields)
    print(pkt)

    return pkt


def main():
    """
    """
    # Read in our config file
    confFile = './config/dbconfig.conf'

    # By doing it this way we ignore the 'enabled' key
    #    but we avoid contortions needed if using
    #    utils.confparsers.parseConfig, so it's worth it
    dbSettings = utils.confparsers.rawParser(confFile)
    dbSettings = workers.confUtils.assignConf(dbSettings['databaseSetup'],
                                              utils.classes.baseTarget,
                                              backfill=True)

    interval = 60

    # Start logging to a file
    utils.logs.setup_logging(logName="./logs/onewireTemps.log", nLogs=10)

    # Set up our signal
    runner = utils.common.HowtoStopNicely()

    idb = utils.database.influxobj(tablename=dbSettings.tablename,
                                   host=dbSettings.host,
                                   port=dbSettings.port,
                                   user=dbSettings.user,
                                   pw=dbSettings.password,
                                   connect=True)

    while runner.halt is False:
        pkt = readAllSensors()
        idb.singleCommit(pkt, table=dbSettings.tablename)

        # Sleep for sleeptime in 1 second intervals
        print("Sleeping for %f seconds..." % (interval))
        i = 0
        if runner.halt is False:
            print("Starting a big sleep")
            # Sleep for bigsleep, but in small chunks to check abort
            for _ in range(interval):
                time.sleep(1)
                if (i + 1) % 30 == 0:
                    print(".", end=None)
                i += 1
                if runner.halt is True:
                    break


if __name__ == "__main__":
    main()
    print("onewireTemps has exited!")
