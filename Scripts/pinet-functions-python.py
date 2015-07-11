#! /usr/bin/env python3
# Part of PiNet https://github.com/pinet/pinet
#
# See LICENSE file for copyright and license details

#PiNet
#pinet-functions-python.py
#Written by Andrew Mulholland
#Supporting python functions for the main pinet script in BASH.
#Written for Python 3.4

#PiNet is a utility for setting up and configuring a Linux Terminal Server Project (LTSP) network for Raspberry Pi's

import sys, os
import logging
import shutil
from subprocess import Popen, PIPE, STDOUT
import textwrap
import time
import urllib.request, urllib.error
import xml.etree.ElementTree as ET

logger = logging.getLogger("pinet")
logger.setLevel(logging.WARNING)

DATA_TRANSFER_FILEPATH = "/tmp/ltsptmp"
PINET_CONF_FILEPATH = "/etc/pinet"

RepositoryBase = "https://github.com/pinet/"
CommitsFeed = "https://github.com/PiNet/PiNet/commits/{ReleaseBranch}.atom"
RepositoryName="pinet"
RawRepositoryBase="https://raw.github.com/pinet/"
Repository=RepositoryBase + RepositoryName
RawRepository=RawRepositoryBase + RepositoryName

_exported = {}
def export(function):
    """Decorator to tag certain functions as exported, meaning
    that they show up as a command, with arguments, when this
    file is run.
    """
    _exported[function.__name__] = function
    return function

def _lines_from_file(filepath, strip=True):
    """Helper function to yield lines from a file, stripping them of
    leading & trailling whitespace by default
    """
    with open(filepath) as f:
        for line in f:
            yield line.strip() if strip else line

def getTextFile(filep):
    """
    Opens the text file and goes through line by line, appending it to the filelist list.
    Each new line is a new object in the list, for example, if the text file was
    ----
    hello
    world
    this is an awesome text file
    ----
    Then the list would be
    ["hello", "world", "this is an awesome text file"]
    Each line is a new object in the list

    """
    return _lines_from_file(filep, strip=False)

def removeN(filelist):
    """
    Removes the final character from every line, this is always /n, aka newline character.
    """
    return [line.rstrip("\n") for line in filelist]

def blankLineRemover(filelist):
    """
    Removes blank lines in the file.
    """
    return [line for line in filelist if line.strip()]

def writeTextFile(filelist, name):
    """
    Writes the final list to a text file.
    Adds a newline character (\n) to the end of every sublist in the file.
    Then writes the string to the text file.
    """
    with open(name, "w") as f:
        f.writelines(line + "\n" for line in filelist)
    
    logger.info("")
    logger.info("------------------------")
    logger.info("File generated")
    logger.info("The file can be found at " + name)
    logger.info("------------------------")
    logger.info("")

def getList(file):
    """
    Creates list from the passed text file with each line a new object in the list
    """
    with open(file) as f:
        return [l.strip("\n") for l in f]

def findReplaceAnyLine(textFile, string, newString):
    """
    Basic find and replace function for entire line.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace the entire line with newString
    """
    return [newString if string in line else line for line in textFile]

def findReplaceSection(textFile, string, newString):
    """
    Basic find and replace function for section.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that exact string with newString
    """
    return [line.replace(string, newString) for line in textFile]
 
def getReleaseChannel(configFilepath="/etc/pinet"):
    Channel = "Stable"
    try:
        configFile = _lines_from_file(configFilepath)
    except FileNotFoundError:
        return "dev"

    search_for = "ReleaseChannel"
    for line in configFile:
        if line.startswith(search_for):
            Channel = line[1 + len(search_for):]
            break

    if Channel == "Stable":
        return "master"
    elif Channel == "Dev":
        return "dev"
    else:
        return "master"

@export
def downloadFile(url="http://bit.ly/pinetinstall1", saveloc="/dev/null"):
    """
    Downloads a file from the internet using a standard browser header.
    Custom header is required to allow access to all pages.
    """
    import traceback
    req = urllib.request.Request(url)
    req.add_header('User-agent', 'Mozilla 5.10')
    try:
        with urllib.request.urlopen(req) as f:
            with open(saveloc, "wb") as text_file:
                text_file.write(f.read())
                return True
    except urllib.error.URLError:
        logger.exception("Problem downloading file")
        return False

_exported['triggerInstall'] = downloadFile

def stripStartWhitespaces(filelist):
    """
    Remove whitespace from start of every line in list.
    """
    return [l.lstrip() for l in filelist]

def stripEndWhitespaces(filelist):
    """
    Remove whitespace from end of every line in list.
    """
    return [l.rstrip() for l in filelist]

def cleanStrings(filelist):
    """
    Removes \n and strips whitespace from before and after each item in the list
    """
    filelist = removeN(filelist)
    filelist = stripStartWhitespaces(filelist)
    return stripEndWhitespaces(filelist)

def getCleanList(filep):
    return cleanStrings(getTextFile(filep))

@export
def compareVersions(local, web):
    """
    Compares 2 version numbers to decide if an update is required.
    """
    web_is_newer = tuple(int(i) for i in web.split(".")) > tuple(int(i) for i in local.split("."))
    returnData(web_is_newer)
    return web_is_newer

_exported['CompareVersion'] = compareVersions

def getConfigParameter(filep, searchfor):
    for line in _lines_from_file(filep):
        if line.startswith(searchfor):
            return line[len(searchfor):]

def returnData(data):
    with open(DATA_TRANSFER_FILEPATH, "w+") as text_file:
        text_file.write(str(data))

def readReturn():
    with open(DATA_TRANSFER_FILEPATH, "r") as text_file:
        print(text_file.read())

#----------------Whiptail functions-----------------
def whiptailBox(type, title, message, returnTF ,height = "8", width= "78"):
    cmd = ["whiptail", "--title", title, "--" + type, message, height, width]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        return False if returnTF else exc.returncode 
    else:
        return True if returnTF else exc.returncode 

def whiptailSelectMenu(title, message, items):
    height, width, other = "16", "78", "5"
    cmd = ["whiptail", "--title", title, "--menu", message ,height, width, other]
    for item in items:
        cmd.extend([item, "a"])
    cmd.append("--noitem")
    p = Popen(cmd,  stderr=PIPE)
    out, err = p.communicate()
    returnCode = p.returncode
    if str(returnCode) == "0":
        return(err)
    else:
        return("Cancel")



#---------------- Main functions -------------------


@export
def replaceLineOrAdd(file, string, newString):
    """
    Basic find and replace function for entire line.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that entire line with newString
    """
    lines = [newString if l == string else l for l in _lines_from_file(file)]
    with open(file, "w") as outf:
        outf.writelines(l + "\n" for l in lines)

@export
def replaceBitOrAdd(file, string, newString):
    """
    Basic find and replace function for section.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that exact string with newString
    """
    lines = [l.replace(string, newString) for l in  _lines_from_file(file)]
    with open(file, "w") as outf:
        outf.writelines(l + "\n" for l in lines)

@export
def internet_on(timeoutLimit, returnType = True):
    """
    Checks if there is an internet connection.
    If there is, return a 0, if not, return a 1
    """
    try:
        urllib.request.urlopen('http://18.62.0.96', timeout=int(timeoutLimit))
        returnData(0)
        return True
    except urllib.error.URLError:  
        pass
    
    try:
        urllib.request.urlopen('http://74.125.228.100', timeout=int(timeoutLimit))
        returnData(0)
        return True
    except:  
        pass
    
    returnData(1)
    return False
_exported['CheckInternet'] = internet_on

@export
def updatePiNet():
    """
    Fetches most recent PiNet and PiNet-functions-python.py
    """
    
    pinet_root = "/home/%s/pinet" % (os.environ['SUDO_USER'])
    try:
        os.remove(pinet_home)
    except OSError: 
        warn("Unable to remove %s", pinet_home)
    
    RawBranch = RawRepository + "/" + getReleaseChannel()
    print("")
    print("----------------------")
    print("Installing update")
    print("----------------------")
    print("")
    download = True
    if not downloadFile(RawBranch + "/pinet", "/usr/local/bin/pinet"):
        download = False
    if not downloadFile(RawBranch + "/Scripts/pinet-functions-python.py", "/usr/local/bin/pinet-functions-python.py"):
        download = False
    
    if download:
        print("----------------------")
        print("Update complete")
        print("----------------------")
        print("")
        returnData(0)
    else:
        print("")
        print("----------------------")
        print("Update failed...")
        print("----------------------")
        print("")
        returnData(1)


def checkUpdate2():
    """
    Grabs the xml commit log to check for releases. Picks out most recent release and returns it.
    """
    temp_filepath = tempfile.mktemp(".txt")
    downloadFile("http://bit.ly/pinetcheckmaster", temp_filepath)
    from xml.dom import minidom
    xmldoc = minidom.parse(temp_filepath)
    version = xmldoc.getElementsByTagName('title')[1].firstChild.nodeValue.strip()
    if version.find("Release") != -1:
        version = version[8:len(version)]
        print(version)
    else:
        print("ERROR")
        print("No release update found!")

def GetVersionNum(data):
    for item in [l.strip() for l in data]:
        if item.startswith("Release"):
            return item[1 + len("Release"):]

@export
def checkUpdate(currentVersion):
    
    def version_from_entry(entry):
        for c in entry.content:
            lines = "".join(ET.fromstring(c.get("value", "")).itertext()).split("\n")
            return GetVersionNum(lines)
    
    if not internet_on(5, False):
        print("No Internet Connection")
        returnData(0)
    
    import feedparser
    feed_url = CommitsFeed.format(ReleaseBranch=getReleaseChannel())
    logger.debug("Feed URL %s", feed_url)
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        thisVersion = version_from_entry(entry)
        logger.debug("Found version %s", thisVersion)
        break
    else:
        raise RuntimeError("Unable to determine version")
    
    if compareVersions(currentVersion, thisVersion):
        whiptailBox("msgbox", "Update detected", "An update has been detected for PiNet. Select OK to view the Release History.", False)
        displayChangeLog(currentVersion)
    else:
        print("No updates found")
        returnData(0)

_exported['CheckUpdate'] = checkUpdate

@export
def checkKernelFileUpdateWeb():
    ReleaseBranch = getReleaseChannel()
    downloadFile(RawRepository +"/" + ReleaseBranch + "/boot/version.txt", "/tmp/kernelVersion.txt")
    user=os.environ['SUDO_USER']
    currentPath="/home/"+user+"/PiBoot/version.txt"
    if (os.path.isfile(currentPath)) == True:
        current = int(getCleanList(currentPath)[0])
        new = int(getCleanList("/tmp/kernelVersion.txt")[0])
        if new > current:
            returnData(1)
            return False
        else:
            returnData(0)
            return True
    else:
        returnData(0)

def checkKernelUpdater():
    ReleaseBranch = getReleaseChannel()
    downloadFile(RawRepository +"/" + ReleaseBranch + "/Scripts/kernelCheckUpdate.sh", "/tmp/kernelCheckUpdate.sh")

    import os.path
    if os.path.isfile("/opt/ltsp/armhf/etc/init.d/kernelCheckUpdate.sh"):

        currentVersion = int(getConfigParameter("/opt/ltsp/armhf/etc/init.d/kernelCheckUpdate.sh", "version=") or 0)
        newVersion = int(getConfigParameter("/tmp/kernelCheckUpdate.sh", "version=") or 0)
        if currentVersion < newVersion:
            installCheckKernelUpdater()
            returnData(1)
            return False
        else:
            returnData(0)
            return True
    else:
        installCheckKernelUpdater()
        returnData(1)
        return False

@export
def installCheckKernelUpdater():
    shutil.copy("/tmp/kernelCheckUpdate.sh", "/opt/ltsp/armhf/etc/init.d/kernelCheckUpdate.sh")
    Popen(['ltsp-chroot', '--arch', 'armhf', 'chmod', '755', '/etc/init.d/kernelCheckUpdate.sh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    process = Popen(['ltsp-chroot', '--arch', 'armhf', 'update-rc.d', 'kernelCheckUpdate.sh', 'defaults'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    process.communicate()

def displayChangeLog(version):
    ReleaseBranch = getReleaseChannel()
    version = "Release " + version
    d = feedparser.parse(Repository +'/commits/' +ReleaseBranch + '.atom')
    releases = []
    for x in range(0, len(d.entries)):
        data = (d.entries[x].content[0].get('value'))
        data = ''.join(xml.etree.ElementTree.fromstring(data).itertext())
        data = data.split("\n")
        thisVersion = "Release " + GetVersionNum(data)
        #thisVersion = data[0].rstrip()
        if thisVersion == version:
            break
        elif x == 10:
            break
        if data[0][0:5] == "Merge":
            continue
        releases.append(data)
    output=[]
    for i in range(0, len(releases)):
        output.append(releases[i][0])
        for z in range(0, len(releases[i])):
            if not z == 0:
                output.append(" - " +releases[i][z])
        output.append("")
    thing = ""
    for i in range(0, len(output)):
        thing = thing + output[i] + "\n"
    cmd = ["whiptail", "--title", "Release history (Use arrow keys to scroll) - " + version, "--scrolltext", "--"+"yesno", "--yes-button", "Install " + output[0], "--no-button", "Cancel", thing, "24", "78"]
    p = Popen(cmd,  stderr=PIPE)
    out, err = p.communicate()
    if p.returncode == 0:
        updatePiNet()
        returnData(1)
        return True
    elif p.returncode == 1:
        returnData(0)
        return False
    else:
        return "ERROR"

@export
def previousImport():
    items = ["passwd", "group", "shadow", "gshadow"]
    #items = ["group",]
    toAdd = []
    for x in range(0, len(items)):
        #migLoc = "/Users/Andrew/Documents/Code/pinetImportTest/" + items[x] + ".mig"
        #etcLoc = "/Users/Andrew/Documents/Code/pinetImportTest/" + items[x]
        migLoc = "/root/move/" + items[x] + ".mig"
        etcLoc = "/etc/" + items[x]
        debug("mig loc " + migLoc)
        debug("etc loc " + etcLoc)
        mig = getList(migLoc)
        etc = getList(etcLoc)
        for i in range(0, len(mig)):
            mig[i] = str(mig[i]).split(":")
        for i in range(0, len(etc)):
            etc[i] = str(etc[i]).split(":")
        for i in range(0, len(mig)):
            unFound = True
            for y in range(0, len(etc)):
                bob = mig[i][0]
                thing = etc[y][0]
                if bob == thing:
                    unFound = False
            if unFound:
                toAdd.append(mig[i])
        for i in range(0, len(toAdd)):
            etc.append(toAdd[i])
        for i in range(0, len(etc)):
            line = ""
            for y in range(0, len(etc[i])):
                line = line  + etc[i][y] + ":"
            line = line[0:len(line) - 1]
            etc[i] = line
        debug(etc)
        writeTextFile(etc, etcLoc)

@export
def importFromCSV(theFile, defaultPassword, test = True):
    import csv
    import os
    from sys import exit
    import crypt
    userData=[]
    if test == "True" or True:
        test = True
    else:
        test = False
    if os.path.isfile(theFile):
        with open(theFile) as csvFile:
            data = csv.reader(csvFile, delimiter=' ', quotechar='|')
            for row in data:
                try:
                    theRow=str(row[0]).split(",")
                except:
                    whiptailBox("msgbox", "Error!", "CSV file invalid!", False)
                    sys.exit()
                user=theRow[0]
                if " " in user:
                    whiptailBox("msgbox", "Error!", "CSV file names column (1st column) contains spaces in the usernames! This isn't supported.", False)
                    returnData("1")
                    sys.exit()
                if len(theRow) >= 2:
                    if theRow[1] == "":
                        password=defaultPassword
                    else:
                        password=theRow[1]
                else:
                    password=defaultPassword
                userData.append([user, password])
            if test:
                thing = ""
                for i in range(0, len(userData)):
                    thing = thing + "Username - " + userData[i][0] + " : Password - " + userData[i][1] + "\n"
                cmd = ["whiptail", "--title", "About to import (Use arrow keys to scroll)" ,"--scrolltext", "--"+"yesno", "--yes-button", "import" , "--no-button", "Cancel", thing, "24", "78"]
                p = Popen(cmd,  stderr=PIPE)
                out, err = p.communicate()
                if p.returncode == 0:
                    for x in range(0, len(userData)):
                        user = userData[x][0]
                        password = userData[x][1]
                        encPass = crypt.crypt(password,"22")
                        cmd = ["useradd", "-m", "-s", "/bin/bash", "-p", encPass, user]
                        p = Popen(cmd,  stderr=PIPE)
                        out, err = p.communicate()
                        fixGroupSingle(user)
                        print("Import of " + user + " complete.")
                    whiptailBox("msgbox", "Complete", "Importing of CSV data has been complete.", False)
                else:
                    sys.exit()
    else:
        print("Error! CSV file not found at " + theFile)

def fixGroupSingle(username):
    groups = ["adm", "dialout", "cdrom", "audio", "users", "video", "games", "plugdev", "input", "pupil"]
    for group in groups:
        subprocess.call(["usermod", "-a", "-G", group, username])

@export
def checkIfFileContains(file, string):
    """
    Does <string> exist in <file>?
    """
    with open(file) as f:
        returnData(int(any(string in line for line in f)))
_exported['checkIfFileContainsString'] = checkIfFileContains

@export
def help(command=None):
    """Display all commands with their description in alphabetical order
    """
    module_doc = sys.modules['__main__'].__doc__ or "PiNet"
    print(module_doc + "\n" + "=" * len(module_doc) + "\n")
    
    for command, function in sorted(_exported.items()):
        print(command)
        doc = function.__doc__
        if doc:
            print(textwrap.indent(textwrap.dedent(doc.strip("\r\n")), "    "))
        else:
            print()

#------------------------------Main program-------------------------

def main(command="help", *args):
    """Dispatch on command name, passing all remaining parameter to the
    module-level function.
    """
    try:
        function = _exported[command]
    except KeyError:
        logger.warn("No such command: %s", command)
    else:
        return function(*args)

if __name__ == '__main__':
    #
    # Set up logging to more verbose logging goes to pinet.log
    # More straightforward logging goes to stdout
    #
    pinet_logger = logging.getLogger("pinet")
    pinet_logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler("pinet.log")
    file_handler.setFormatter(logging.Formatter("%(levelname)s: %(funcName)s - %(message)s"))
    file_handler.setLevel(logging.DEBUG)
    pinet_logger.addHandler(file_handler)
    
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)
    pinet_logger.addHandler(stdout_handler)
    
    sys.exit(main(*sys.argv[1:]))
