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
try:
    import crypt
except ImportError:
    crypt = None
import csv
import inspect
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
DEFAULT_RELEASE_CHANNEL = "Stable"
DEFAULT_GIT_BRANCH = "master"

RepositoryBase = "https://github.com/pinet/"
CommitsFeed = "https://github.com/PiNet/PiNet/commits/{ReleaseBranch}.atom"
RepositoryName="pinet"
RawRepositoryBase="https://raw.github.com/pinet/"
Repository=RepositoryBase + RepositoryName
RawRepository=RawRepositoryBase + RepositoryName

#
# TODO: Deprecated functions; left here for now
#
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
    return list(_lines_from_file(filep, strip=False))

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
#
# End of deprecated functions
#

_exported = {}
def export(function):
    """Decorator to tag certain functions as exported, meaning
    that they show up as a command, with arguments, when this
    file is run.
    """
    _exported[function.__name__] = function
    return function

def _lines_from_file(filepath, strip=True):
    """Generate the lines of a file one at a time
    
    :returns: a generator over each line of the file
    :filepath: the full path to the file
    :strip: leading & trailing whitespace are stripped unless this is False
    
    Wrap the common case of reading all lines from a file so the
    file is opened & closed via a context manager. This is mostly
    useful when doing this inside some other block below.
    """
    with open(filepath) as f:
        for line in f:
            if strip:
                yield line.strip()
            else:
                yield line

def list_from_file(filepath, strip=True, ignore_blanks=True):
    """Return a list of strings, each corresponding to a line in <filepath>
    
    :returns: a list of lines
    :strip: Leading & trailing whitespace are stripped unless this is False
    :ignore_blanks: Lines which are empty are skipped unless this is False
    """
    lines = []
    for line in _lines_from_file(filepath, strip=strip):
        if ignore_blanks and line == "":
            continue
        lines.append(line)
    return lines

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

def findReplaceAnyLine(textFile, string, newString):
    """
    Basic find and replace function for entire line.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace the entire line with newString
    """
    lines = []
    for line in textFile:
        if string in line:
            lines.append(newString)
        else:
            lines.append(lines)
    return lines

def findReplaceSection(textFile, string, newString):
    """
    Basic find and replace function for section.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that exact string with newString
    """
    return [line.replace(string, newString) for line in textFile]
 
def _read_configuration(config_filepath="/etc/pinet"):
    """Read a configuration file, typically /etc/pinet, file into a dictionary
    
    :returns: a dictionary corresponding to the configuration file
    :config_filepath: the path to the configuration file
    
    /etc/pinet consists of a series of keyword=value lines (with some
    repeats, it appears). Read these into a dictionary, ignoring all
    but the first instance if any key repeats.
    """
    configuration = dict()
    try:
        for line in _lines_from_file(config_filepath, strip=True):
            if line:
                key, _, value = line.partition("=")
                if not key:
                    continue
                elif key in configuration:
                    logger.warn("Key %s=%s already found in %s with value %s", key, value, config_filepath, configuration[key])
                else:
                    configuration[key] = value
    except OSError as exc:
        logger.exception("Unable to read configuration from %s", config_filepath)

    return configuration
    
def getReleaseChannel(configFilepath="/etc/pinet"):
    """Return the git branch corresponding to the active release channel
    
    :returns: a string representing a git branch
    :configFilepath: the path to the PiNet configuration file
    
    When installing PiNet you can select the Stable or the Development
    channel. These correspond to the master and dev branches respectively
    in the PiNet git repo.
    """
    channel_branches = {
        "Stable" : "master",
        "Dev" : "dev"
    }
    configuration = _read_configuration(configFilepath)
    
    #
    # Warn if no release channel was found, and use a default
    #
    if "ReleaseChannel" not in configuration:
        logger.warn("No release channel found in %s; assuming %s", configFilepath, DEFAULT_RELEASE_CHANNEL)
        release_channel = DEFAULT_RELEASE_CHANNEL
    else:
        release_channel = configuration['ReleaseChannel']
    
    #
    # Warn if no branch found to match the release channel, and use a default
    #
    if release_channel not in channel_branches:
        logger.warn("No branch corresponds to release channel %s; assuming %s", release_channel, DEFAULT_GIT_BRANCH)
        return DEFAULT_GIT_BRANCH
    else:
        return channel_branches[release_channel]

@export
def downloadFile(url="http://bit.ly/pinetinstall1", saveloc=os.devnull):
    """Download a file and save it to the filesystem
    
    :returns: True if successful, False otherwise
    :url: the URL to download from
    :saveloc: the filesystem location to save to

    NB a custom header tweaks the User-agent to allow access to all pages   
    """
    req = urllib.request.Request(url)
    req.add_header('User-agent', 'Mozilla 5.10')
    try:
        with urllib.request.urlopen(req) as f:
            with open(saveloc, "wb") as text_file:
                text_file.write(f.read())
                return True
    except urllib.error.URLError:
        logger.exception("Problem downloading %s to %s", url, saveloc)
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

def _version_from_string(version_string):
    """Convert a 'x.y.z' version string into the equivalent tuple
    
    Assumes an integer version, eg 1.2.10, as all version segments
    will be compared numerically via Python's usual tuple-comparison
    semantics
    """
    return tuple(int(segment) for segment in version_string.split("."))

@export
def compareVersions(local, web):
    """
    Compares 2 version numbers to decide if an update is required.
    """
    web_version = _version_from_string(web)
    local_version = _version_from_string(local)
    web_is_newer = web_version > local_version
    
    returnData(int(web_is_newer))
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
    for url in ['http://18.62.0.96', 'http://74.125.228.100']:
        try:
            urllib.request.urlopen(url, timeout=int(timeoutLimit))
            returnData(0)
            return True
        except urllib.error.URLError:  
            continue
    
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
        os.remove(pinet_root)
    except OSError: 
        logger.warn("Unable to remove %s", pinet_root)
    
    RawBranch = RawRepository + "/" + getReleaseChannel()
    print("")
    print("----------------------")
    print("Installing update")
    print("----------------------")
    print("")
    
    downloads = [
        (RawBranch + "/pinet", "/usr/local/bin/pinet"),
        (RawBranch + "/Scripts/pinet-functions-python.py", "/usr/local/bin/pinet-functions-python.py")
    ]
    for url, filepath in downloads:
        if downloadFile(url, filepath):
            logger.info("Downloaded %s to %s", url, filepath)
        else:
            logger.error("Failed to download %s to %s", url, filepath)
            print("")
            print("----------------------")
            print("Update failed...")
            print("----------------------")
            print("")
            returnData(1)
            return
    else:
        print("----------------------")
        print("Update complete")
        print("----------------------")
        print("")
        returnData(0)

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

def _commits_from_feed():
    """Given the release branch we're on, determine the RSS feed for commits
    and generate it, one line at a time. This is usually to parse out the
    current release.
    """
    feed_url = CommitsFeed.format(ReleaseBranch=getReleaseChannel())
    logger.debug("Reading commits from %s", feed_url)
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        for content in entry.content:
            for line in "".join(ET.fromstring(c.get("value", "")).itertext()).split("\n"):
                yield line

@export
def checkUpdate(currentVersion):
    
    if not internet_on(5, False):
        print("No Internet Connection")
        returnData(0)
    
    for line in commits_from_feed():
        if line.startswith("Release"):
            thisVersion = line[1 + len("Release"):]
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
    """Add <username> into specific groups
    """
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
        signature = inspect.signature(function)
        print("{}{}".format(command, signature))
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
