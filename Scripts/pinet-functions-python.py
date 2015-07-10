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


from logging import debug, info, warning, basicConfig, INFO, DEBUG, WARNING
basicConfig(level=WARNING)
import sys, os
from subprocess import Popen, PIPE
import time

RepositoryBase="https://github.com/pinet/"
RepositoryName="pinet"
RawRepositoryBase="https://raw.github.com/pinet/"
Repository=RepositoryBase + RepositoryName
RawRepository=RawRepositoryBase + RepositoryName

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
    with open(filep) as f:
        return list(f)

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
    
    info("")
    info("------------------------")
    info("File generated")
    info("The file can be found at " + name)
    info("------------------------")
    info("")

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
        configFile = getList(configFilepath)
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

def downloadFile(url="http://bit.ly/pinetinstall1", saveloc="/dev/null"):
    """
    Downloads a file from the internet using a standard browser header.
    Custom header is required to allow access to all pages.
    """
    import traceback
    import urllib.request
    req = urllib.request.Request(url)
    req.add_header('User-agent', 'Mozilla 5.10')
    try:
        with urllib.request.urlopen(req) as f:
            text_file = open(saveloc, "wb")
            text_file.write(f.read())
            text_file.close()
            return True
    except:
        print (traceback.format_exc())
        return False
triggerInstall = downloadFile

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

def compareVersions(local, web):
    """
    Compares 2 version numbers to decide if an update is required.
    """
    web = str(web).split(".")
    local = str(local).split(".")
    if int(web[0]) > int(local[0]):
        returnData(1)
        return True
    else:
        if int(web[1]) > int(local[1]):
            returnData(1)
            return True
        else:
            if int(web[2]) > int(local[2]):
                returnData(1)
                return True
            else:
                returnData(0)
                return False
CompareVersion = compareVersions

def getConfigParameter(filep, searchfor):
    textFile = getTextFile(filep)
    textFile = stripEndWhitespaces(textFile)
    value = ""
    for i in range(0,len(textFile)):
        #print(textFile[i])
        found = textFile[i].find(searchfor)
        if (found != -1):
            #print(textFile[i])
            bob = found+len(searchfor)
            jill = len(searchfor)
            value = textFile[i][found+len(searchfor):len(textFile[i])]

    if value == "":
        value = "None"

    return value

#def selectFile(start = "/home/"+os.environ['SUDO_USER']+"/"):
#    pass
def returnData(data):
    with open("/tmp/ltsptmp", "w+") as text_file:
        text_file.write(str(data))
    return
    #return fileLoc

def readReturn():
    with open("/tmp/ltsptmp", "r") as text_file:
        print(text_file.read())

#----------------Whiptail functions-----------------
def whiptailBox(type, title, message, returnTF ,height = "8", width= "78"):
    cmd = ["whiptail", "--title", title, "--"+type, message, height, width]
    p = Popen(cmd,  stderr=PIPE)
    out, err = p.communicate()

    if returnTF:
        if p.returncode == 0:
            return True
        elif p.returncode == 1:
            return False
        else:
            return "ERROR"
    else:
        return p.returncode

def whiptailSelectMenu(title, message, items):
    height, width, other = "16", "78", "5"
    cmd = ["whiptail", "--title", title, "--menu", message ,height, width, other]
    itemsList = ""
    for x in range(0, len(items)):
        cmd.append(items[x])
        cmd.append("a")
    cmd.append("--noitem")
    p = Popen(cmd,  stderr=PIPE)
    out, err = p.communicate()
    returnCode = p.returncode
    if str(returnCode) == "0":
        return(err)
    else:
        return("Cancel")



#---------------- Main functions -------------------


def replaceLineOrAdd(file, string, newString):
    """
    Basic find and replace function for entire line.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that entire line with newString
    """
    textfile = getList(file)
    textfile = findReplaceAnyLine(textfile, string, newString)
    writeTextFile(textfile, file)

def replaceBitOrAdd(file, string, newString):
    """
    Basic find and replace function for section.
    Pass it a text file in list form and it will search for strings.
    If it finds a string, it will replace that exact string with newString
    """
    textfile = getList(file)
    textfile = findReplaceSection(textfile, string, newString)
    writeTextFile(textfile, file)

def internet_on(timeoutLimit, returnType = True):
    """
    Checks if there is an internet connection.
    If there is, return a 0, if not, return a 1
    """
    import urllib.request
    #print("Checking internet")
    try:
        response=urllib.request.urlopen('http://18.62.0.96',timeout=int(timeoutLimit))
        returnData(0)
        #print("returning 0")
        return True
    except:  pass
    try:
        response=urllib.request.urlopen('http://74.125.228.100',timeout=int(timeoutLimit))
        returnData(0)
        #print("returning 0")
        return True
    except:  pass
    #print("Reached end, no internet")
    returnData(1)
    return False
CheckInternet = internet_on

def updatePiNet():
    """
    Fetches most recent PiNet and PiNet-functions-python.py
    """
    ReleaseBranch = getReleaseChannel()
    try:
        os.remove("/home/"+os.environ['SUDO_USER']+"/pinet")
    except: pass
    print("")
    print("----------------------")
    print("Installing update")
    print("----------------------")
    print("")
    download = True
    if not downloadFile(RawRepository +"/" + ReleaseBranch + "/pinet", "/usr/local/bin/pinet"):
        download = False
    if not downloadFile(RawRepository +"/" + ReleaseBranch + "/Scripts/pinet-functions-python.py", "/usr/local/bin/pinet-functions-python.py"):
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

    loc = "/tmp/raspiupdate.txt"
    downloadFile("http://bit.ly/pinetcheckmaster", loc)
    from xml.dom import minidom
    xmldoc = minidom.parse(loc)
    version = xmldoc.getElementsByTagName('title')[1].firstChild.nodeValue
    version = cleanStrings([version,])[0]
    if version.find("Release") != -1:
        version = version[8:len(version)]
        print(version)
    else:
        print("ERROR")
        print("No release update found!")

def GetVersionNum(data):
    for i in range(0, len(data)):
        bob = data[i][0:8]
        if data[i][0:7] == "Release":
            bob = data[i]
            version = str(data[i][8:len(data[i])]).rstrip()
            return version


def checkUpdate(currentVersion):
    ReleaseBranch = getReleaseChannel()
    if not internet_on(5, False):
        print("No Internet Connection")
        returnData(0)
    import feedparser
    import xml.etree.ElementTree
    downloadFile("http://bit.ly/pinetCheckCommits", "/dev/null")
    d = feedparser.parse(Repository +'/commits/' +ReleaseBranch + '.atom')
    releases = []
    data = (d.entries[0].content[0].get('value'))
    data = ''.join(xml.etree.ElementTree.fromstring(data).itertext())
    data = data.split("\n")
    thisVersion = GetVersionNum(data)
    #thisVersion = data[0].rstrip()
    #thisVersion = thisVersion[8:len(thisVersion)]

    if compareVersions(currentVersion, thisVersion):
        whiptailBox("msgbox", "Update detected", "An update has been detected for PiNet. Select OK to view the Release History.", False)
        displayChangeLog(currentVersion)
    else:
        print("No updates found")
        #print(thisVersion)
        #print(currentVersion)
        returnData(0)
CheckUpdate = checkUpdate


def checkKernelFileUpdateWeb():
    ReleaseBranch = getReleaseChannel()
    downloadFile(RawRepository +"/" + ReleaseBranch + "/boot/version.txt", "/tmp/kernelVersion.txt")
    import os.path
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

        currentVersion = int(getConfigParameter("/opt/ltsp/armhf/etc/init.d/kernelCheckUpdate.sh", "version="))
        newVersion = int(getConfigParameter("/tmp/kernelCheckUpdate.sh", "version="))
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

def installCheckKernelUpdater():
    import shutil
    from subprocess import Popen, PIPE, STDOUT
    shutil.copy("/tmp/kernelCheckUpdate.sh", "/opt/ltsp/armhf/etc/init.d/kernelCheckUpdate.sh")
    Popen(['ltsp-chroot', '--arch', 'armhf', 'chmod', '755', '/etc/init.d/kernelCheckUpdate.sh'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    process = Popen(['ltsp-chroot', '--arch', 'armhf', 'update-rc.d', 'kernelCheckUpdate.sh', 'defaults'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    process.communicate()

def displayChangeLog(version):
    ReleaseBranch = getReleaseChannel()
    version = "Release " + version
    import feedparser
    import xml.etree.ElementTree
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
    for x in range(0, len(groups)):
        cmd = ["usermod", "-a", "-G", groups[x], username]
        p = Popen(cmd,  stderr=PIPE)
        out, err = p.communicate()

def checkIfFileContains(file, string):
    """
    Simple function to check if a string exists in a file.
    """
    with open(file) as f:
        returnData(int(any(string in line for line in f)))

def _test(*args, **kwargs):
    print("_test", args, kwargs)
    
#------------------------------Main program-------------------------

def main(command=None, *args):
    if not command:
        print("This python script does nothing on its own, it must be passed stuff")
        return

    mod = sys.modules['__main__']
    print(mod)
    try:
        function = getattr(mod, command)
    except AttributeError:
        print("No such command: {}".format(command))
    
    function(*args)

if __name__ == '__main__':
    main(*sys.argv[1:])
