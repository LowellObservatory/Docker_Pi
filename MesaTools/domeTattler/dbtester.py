# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 9 Apr 2020
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
    tstr = "Searching between %s and %s, " % (pdata[qstr].index.min(),
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


def main():
    """
    """
    debug = True
    confFile = 'MesaTools/domeTattler/domeTattler.conf'
    dtconfig, picam, email, dbq = parseConf(confFile)

    # This is the name of the function that should already exist either
    #   as an import or defined in this file; it's specific to each
    #   query, since that gives the most flexibility to report per situation
    try:
        querproc = dtconfig['queryprocessing']
    except KeyError:
        print("WARNING: Query processing function is undefined!")
        querproc = None

    if querproc is not None:
        try:
            querfunc = eval(querproc)
        except NameError:
            print("WARNING: Query processing function %s not found!" %
                  (querproc))
            querfunc = None

    pdata = gatherStats(dbq, debug=debug)
    if querfunc is not None:
        databaseReport = querfunc(dtconfig['querykey'], pdata)

    print("=====")
    print(databaseReport)
    print("=====")


if __name__ == "__main__":
    main()
