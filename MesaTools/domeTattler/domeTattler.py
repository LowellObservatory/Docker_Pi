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
import datetime as dt

import pytz
import schedule

import johnnyfive as j5
try:
    import picamhelpers as pch
except ImportError:
    print("WARNING: PiCamHelpers not found! Disabling Pi Camera stuff.")
    pch = None

from ligmos.workers import confUtils
from ligmos.utils import classes as lc
from ligmos.utils import confparsers, database
from ligmos.utils import logs, common, ephemera


def parseConf(confFile):
    """
    """
    # By doing it this way we ignore the 'enabled' key
    #    but we avoid contortions needed if using
    #    utils.confparsers.parseConfig, so it's worth it
    allSettings = confparsers.rawParser(confFile)

    # By parsing the 'tattleConfig' section we can map to the relevant
    #   sections in the config file directly, and avoid hardcoded stuff
    #   except for the name of this particular section and these keys
    dtc = allSettings['tattleConfig']
    pconf = allSettings[dtc['camkey']]
    econf = allSettings[dtc['emailkey']]
    cquer = allSettings[dtc['querykey']]

    # Assign the configuration sections to the relevant classes
    if pch is not None:
        camSettings = confUtils.assignConf(pconf, pch.classes.piCamSettings)
    else:
        camSettings = None
    emailSettings = confUtils.assignConf(econf, j5.classes.emailSNMP)

    # This allows us to pull from multiple databases and multiple queries,
    #   even though the 'querykey' in the main config section only accepts one
    #   (for now)
    qukey = "q_"
    allSections = allSettings.sections()
    qList = [each for each in allSections if each.lower().startswith(qukey)]

    # This one is a little more complex, since the database info is
    #   stuffed into the actual query class and that's what's passed around
    querDict = {}
    for each in qList:
        cquer = allSettings[each]
        try:
            querySettings = confUtils.assignConf(cquer, lc.databaseQuery)
            whichdb = querySettings.database

            dconf = allSettings[whichdb]
            databaseSettings = confUtils.assignConf(dconf, lc.baseTarget)
            querySettings.database = databaseSettings
        except KeyError:
            print("WARNING: Database %s not found in config file!" % (whichdb))
            querySettings.database = None

        querDict.update({each: querySettings})

    # Read in the footer file as a text string
    try:
        with open(emailSettings.footer, 'r') as f:
            emailSettings.footer = f.read()
        print("Email footer found!")
        print("===")
        print(emailSettings.footer)
        print("===")
    except (OSError, IOError):
        print("Email footer not found! Moving on...")
        emailSettings.footer = None

    return dtc, camSettings, emailSettings, querDict


def gatherStats(queries, debug=True):
    """
    """
    pdata = {}

    for query in queries:
        res = database.getResultsDataFrame(queries[query], debug=debug)
        pdata.update({query: res})

    print("Queries complete!")

    return pdata


def mesacryotiger(qstr, pdata):
    """
    No error checking, though it could be added if someone gets worried about
    the database keys changing from the hardcoded names.
    """
    # Query specific manipulations
    tstr = "\nCryotiger Status:\n"
    tstr += "%s to %s, " % (pdata[qstr].index.min(),
                            pdata[qstr].index.max())
    tstr += "%d records found.\n" % (len(pdata[qstr]['CompressorTemp']))

    cstr = "Compressor:"
    cstr += "\n\t%.2f | %.2f +/- %.2f | %.2f" %\
            (round(pdata[qstr]['CompressorTemp'].min(), 2),
             round(pdata[qstr]['CompressorTemp'].mean(), 2),
             round(pdata[qstr]['CompressorTemp'].std(), 2),
             round(pdata[qstr]['CompressorTemp'].max(), 2))

    astr = "Air:"
    astr += "\n\t%.2f | %.2f +/- %.2f | %.2f" %\
            (round(pdata[qstr]['AirTemp'].min(), 2),
             round(pdata[qstr]['AirTemp'].mean(), 2),
             round(pdata[qstr]['AirTemp'].std(), 2),
             round(pdata[qstr]['AirTemp'].max(), 2))

    diff = pdata[qstr]['CompressorTemp'] - pdata[qstr]['AirTemp']
    dstr = "Delta:"
    dstr += "\n\t%.2f | %.2f +/- %.2f | %.2f" %\
            (round(diff.min(), 2),
             round(diff.mean(), 2), round(diff.std(), 2),
             round(diff.max(), 2))

    finalStr = tstr + "\n" + cstr + "\n" + astr + "\n" + dstr

    return finalStr


def assembleEmail(emailConfig, picam,
                  dbq=None, querfunc=None, querkey=None,
                  squashEmail=False, debug=False):
    """
    """
    # Sometimes we have a server that's set up in UTC,
    #   so we have to do dumb things so account for that
    when = dt.datetime.now()
    when = when.astimezone(tz=pytz.timezone("America/Phoenix"))
    whendate = str(when.date())
    whenutc = when.astimezone(tz=pytz.timezone("UTC"))

    mesa = ephemera.observingSite(sitename='mesa')
    sunalt = round(mesa.sunmoon.sun_alt, 2)
    moonalt = round(mesa.sunmoon.moon_alt, 2)

    subject = "Dome Checkup: %s" % (whendate)

    body = "Time (UTC): %s\n" % (whenutc.strftime("%Y%m%d %H:%M:%S"))
    body += "Time (Local): %s\n" % (when.strftime("%Y%m%d %H:%M:%S"))
    body += "\n"
    body += "Sun Altitude (deg): %.2f\n" % (sunalt)
    body += "Moon Altitude (deg): %.2f\n" % (moonalt)

    if querfunc is not None:
        pdata = gatherStats(dbq, debug=debug)
        databaseReport = querfunc(querkey, pdata)
        body += databaseReport

    # Now append the rest of the stuff if there is some
    if emailConfig.footer is not None:
        body += "\n\n"
        body += str(emailConfig.footer)

    if emailConfig is not None and squashEmail is False:
        eFrom = emailConfig.user
        eTo = emailConfig.toaddr

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
    debug = True
    squashEmail = False

    # Start logging to a file
    try:
        logs.setup_logging(logName="./logs/domeTattler.log", nLogs=10)
    except OSError as err:
        print("WARNING: Logging setup failed!")
        print(str(err))

    confFile = 'MesaTools/domeTattler/domeTattler.conf'
    dtconfig, picam, email, dbq = parseConf(confFile)

    # This is the name of the function that should already exist either
    #   as an import or defined in this file; it's specific to each
    #   query, since that gives the most flexibility to report per situation
    try:
        querproc = dtconfig['queryprocessing']
        try:
            querfunc = eval(querproc)
        except NameError:
            print("WARNING: Query processing function %s not found!" %
                  (querproc))
            querfunc = None
    except KeyError:
        print("WARNING: Query processing function is undefined!")
        querproc = None

    # Set up our signal
    runner = common.HowtoStopNicely()

    # Create our actual schedule of when to send a picture
    #   NOTE: The time must match the timezone of the server!
    #     (which could be UTC already)
    sched = schedule.Scheduler()
    timesched = dtconfig['notificationtime']
    schedTag = "MorningDomeCheck"
    sched.every().day.at(timesched).do(assembleEmail,
                                       email, picam,
                                       dbq=dbq,
                                       querkey=dtconfig['querykey'],
                                       querfunc=querfunc,
                                       debug=debug,
                                       squashEmail=squashEmail).tag(schedTag)

    while runner.halt is False:
        sched.run_pending()

        for job in sched.jobs:
            remaining = (job.next_run - dt.datetime.now()).total_seconds()
            if int(round(remaining, 0)) % 300 == 0 or remaining <= 15:
                print("    %s in %.2f minutes" % (job.tags, remaining/60.))

        time.sleep(1)


if __name__ == "__main__":
    main()
    print("domeTattler has exited!")
