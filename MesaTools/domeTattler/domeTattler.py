# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 1 Apr 2020
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import math
import time
import imghdr
from datetime import datetime as dt

import pytz
import ephem
import schedule

import johnnyfive as j5
import picamhelpers as pch

from ligmos.utils import logs, common
from ligmos.utils import confparsers
from ligmos.utils import classes as lc
from ligmos.workers import confUtils


def parseConf(confFile):
    """
    """
    # By doing it this way we ignore the 'enabled' key
    #    but we avoid contortions needed if using
    #    utils.confparsers.parseConfig, so it's worth it
    allSettings = confparsers.rawParser(confFile)

    # These are hardcoded so watch out.
    pconf = allSettings['picam']
    econf = allSettings['email']
    dconf = allSettings['databaseSetup']

    camSettings = confUtils.assignConf(pconf, pch.classes.piCamSettings)

    emailSettings = confUtils.assignConf(econf, j5.classes.emailSNMP)

    databaseSettings = confUtils.assignConf(dconf, lc.databaseQuery)

    return camSettings, emailSettings, databaseSettings


def genEphem():
    """
    Hardcoded to generate relevant ephemeris info for
    Anderson Mesa
    """
    # Set up the ephemera/observing site info for solar angles
    site = ephem.Observer()
    site.lat = '35.096944'
    site.lon = '-111.535833'
    site.elevation = 2163
    site.name = "Lowell Observatory Anderson Mesa"

    sun = ephem.Sun()
    mon = ephem.Moon()
    sun.compute(site)
    mon.compute(site)

    return round(math.degrees(sun.alt), 4), round(math.degrees(mon.alt), 4)


def assembleEmail(emailConfig, picam, squashEmail=False):
    """
    """
    when = dt.now()
    whendate = str(when.date())
    whenutc = when.astimezone(tz=pytz.timezone("UTC"))

    sunalt, moonalt = genEphem()

    subject = "Dome Checkup: %s" % (whendate)

    body = "Time (UTC): %s\n" % (whenutc.strftime("%Y%m%d %H:%M:%S"))
    body += "Time (Local): %s\n" % (when.strftime("%Y%m%d %H:%M:%S"))
    body += "\nSun Altitude (deg): %f\nMoon Altitude (deg): %f\n" % (sunalt,
                                                                     moonalt)

    body += "TODO: Query the database for 24h cryotiger health checks."
    body += "That'll get done...soon?\n\n"

    if emailConfig is not None and squashEmail is False:
        eFrom = emailConfig.user
        eTo = emailConfig.toaddr

        # Read in the footer, if there is one
        if emailConfig.footer is None:
            footer = ""
        else:
            footer = str(emailConfig.footer)

        # Now append the rest of the stuff if there is some
        if footer != "":
            body += "\n\n"
            body += footer

        msg = j5.email.constructMail(subject, body, eFrom, eTo,
                                     fromname=emailConfig.fromname)

        if picam is not None:
            snapname = pch.capture.piCamCapture(picam, picam.savepath)

            if snapname is not None:
                with open(snapname, 'rb') as pisnap:
                    piimg = pisnap.read()
                    msg.add_attachment(piimg, maintype='image',
                                       subtype=imghdr.what(None, piimg),
                                       filename="DomeCheck.png")
            else:
                print("PiCamera capture failed!")

        j5.email.sendMail(msg,
                          smtploc=emailConfig.host,
                          port=emailConfig.port,
                          user=emailConfig.user,
                          passw=emailConfig.password)
        print("Email sent!")


def main():
    interval = 60
    squashEmail = False

    # Read in our config file
    confFile = './config/domeTattler.conf'

    picam, email, db = parseConf(confFile)

    # Start logging to a file
    logs.setup_logging(logName="./logs/domeTattler.log", nLogs=10)

    # Set up our signal
    runner = common.HowtoStopNicely()

    # Create our actual schedule of when to send a picture
    #   NOTE: The time must match the timezone of the server!
    #   Convert yourself to UTC if you must, it's just easier.
    sched = schedule.Scheduler()
    timesched = "05:25"
    sched.every().day.at(timesched).do(assembleEmail,
                                       email, picam, squashEmail=squashEmail)

    while runner.halt is False:
        # Check our schedule to see if we have to do anything
        sched.run_pending()
        for job in sched.jobs:
            remaining = (job.next_run - dt.now()).total_seconds()
            print("    %s in %f seconds" % (job.tags, remaining))

        # Sleep for interval in 1 second increments
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
    print("domeTattler has exited!")
