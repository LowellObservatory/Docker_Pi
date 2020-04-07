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

import time
import imghdr

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


def assembleEmail(emailConfig, picam):
    """
    """
    subject = "Dome Status"
    body = "Fill me up"

    if emailConfig is not None:
        eFrom = emailConfig.user
        eTo = emailConfig.toaddr

        # Read in the footer, if there is one
        if emailConfig.footer is None:
            footer = ""
        else:
            footer = str(emailConfig.footer)

        # Now append the rest of the stuff
        body += "\n\n"
        body += footer
        body += "\n\nYour 3D pal, \nThe Great Printzini"

        msg = j5.email.constructMail(subject, body, eFrom, eTo,
                                     fromname=emailConfig.fromname)

        if picam is not None:
            snapname = pch.capture.piCamCapture(picam, picam.savepath)

            if snapname is not None:
                with open(snapname, 'rb') as pisnap:
                    piimg = pisnap.read()
                    msg.add_attachment(piimg, maintype='image',
                                       subtype=imghdr.what(None, piimg),
                                       filename="Dome31MorningCheck.png")
            else:
                print("PiCamera capture failed!")

    return msg


def morningSender(emailConfig, msg, squashEmail=False):
    """
    """
    # If squashEmail is True, email will be None
    if emailConfig is not None and squashEmail is False:
        j5.email.sendMail(msg,
                          smtploc=emailConfig.host,
                          port=emailConfig.port,
                          user=emailConfig.user,
                          passw=emailConfig.password)

        print("Email sent!")


def main():
    interval = 60

    # Read in our config file
    confFile = './config/domeTattler.conf'

    picam, email, db = parseConf(confFile)

    # Start logging to a file
    logs.setup_logging(logName="./logs/domeTattler.log", nLogs=10)

    # Set up our signal
    runner = common.HowtoStopNicely()

    while runner.halt is False:
        # Schedule the email for the morning


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
    print("domeTattler has exited!")
