#------------------------------------------------------------------------------
# File          : ZipCheck.py
# Package       : rpmlint
# Author        : Ville Skyttä
# Created on    : Thu Oct 30 00:14:45 EET 2003
# Version       : $Id$
# Purpose       : Verify Zip/Jar file correctness
#------------------------------------------------------------------------------

from Filter import *
import AbstractCheck
import Config
import os
import re
import stat
import zipfile

zip_regex=re.compile('\.(zip|[ewj]ar)$')
jar_regex=re.compile('\.[ewj]ar$')
classpath_regex=re.compile('^\s*Class-Path\s*:', re.M | re.I)

want_indexed_jars = Config.getOption('UseIndexedJars', 1)

class ZipCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "ZipCheck")

    def check(self, pkg):
        for i in pkg.getFilesInfo():
            f = pkg.dirName() + i[0]
            if zip_regex.search(f) and \
                   stat.S_ISREG(os.lstat(f)[stat.ST_MODE]) and \
                   zipfile.is_zipfile(f):
                zip = None
                try:
                    zip = zipfile.ZipFile(f, 'r')
                    badcrc = zip.testzip()
                    if badcrc:
                        printError(pkg, 'bad-crc-in-zip: %s' % badcrc, i[0])
                    compressed = 0
                    for zinfo in zip.infolist():
                        if zinfo.compress_type != zipfile.ZIP_STORED:
                            compressed = 1
                            break
                    if not compressed:
                        printWarning(pkg, 'uncompressed-zip', i[0])

                    # additional jar checks
                    if jar_regex.search(f):
                        try:
                            mf = zip.read('META-INF/MANIFEST.MF')
                            if classpath_regex.search(mf):
                                printWarning(pkg, 'class-path-in-manifest', i[0])
                        except KeyError:
                            printError(pkg, 'no-jar-manifest', i[0])
                        try:
                            zinfo = zip.getinfo('META-INF/INDEX.LIST')
                            if not want_indexed_jars:
                                printWarning(pkg, 'jar-indexed', i[0])
                        except KeyError:
                            if want_indexed_jars:
                                printWarning(pkg, 'jar-not-indexed', i[0])
                            pass
                finally:
                    zip and zip.close()


check = ZipCheck()

if Config.info:
    addDetails(
'bad-crc-in-zip',
'''The reported file in the zip fails the CRC check. Usually this is a
sign of a corrupt zip file.''',

'uncompressed-zip',
'''The zip file is not compressed.''',

'class-path-in-manifest',
'''The META-INF/MANIFEST file in the jar contains a hardcoded Class-Path.
These entries do not work with older Java versions and even if they do work,
they are inflexible and usually cause nasty surprises.''',

'no-jar-manifest',
'''The jar file does not contain a META-INF/MANIFEST file.''',

'jar-indexed',
'''The jar file is indexed, ie. it contains the META-INF/INDEX.LIST file.
These files are known to cause problems with some older Java versions.''',

'jar-not-indexed',
'''The jar file is not indexed, ie. it does not contain the META-INF/INDEX.LIST
file.  Indexed jars speed up the class searching process of classloaders
in some situations.''',
)

# ZipCheck.py ends here