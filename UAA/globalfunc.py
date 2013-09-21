# -*- coding: utf-8 -*-
from datetime import datetime
import sys
import time
import re
import localconfig
import traceback
import pywikibot
from pywikibot.data import api

site = pywikibot.Site('en', 'wikipedia')


def currentTime():
    return pywikibot.Timestamp.utcnow().totimestampformat() + 'Z'


def getEditCount(user):
    try:
        username = pywikibot.User(site, user)
        if username.editCount() == 0:
            return False
        else:
            return True
    except:
        return None


def checkBlocked(user):
    try:
        username = pywikibot.User(site, user)
        return username.isBlocked()
    except:
        return None


def checkRegisterTime(user, maxDays):
    """Returns True if the given user is more than maxDays old, else False."""
    maxSeconds = maxDays * 24 * 60 * 60
    params = {"action": "query", "list": "users", "ususers": user, "format": "json", "usprop": "registration"}
    req = api.Request(site=site, **params)
    result = req.submit()
    reg = result["query"]["users"][0]["registration"]
    then = time.strptime(reg, "%Y-%m-%dT%H:%M:%SZ")
    now = time.gmtime()
    thenSeconds = time.mktime(then)
    nowSeconds = time.mktime(now)
    if thenSeconds < nowSeconds - maxSeconds:
        return True
    return False


def searchlist(line, listtype):
    try:
        line=line.decode("utf-8")
    except:
        pass
    if line == "":
        return
    if listtype == "bl":
        i=0
        while i < len(bl):
            if bl[i].lower().split(":")[0] != "":
                check = re.search(bl[i].lower().split(":")[0], line.lower())
            else:
                check = None
            if not (check == "None" or check == None):
                return [True, bl[i].split(":")[0], ' '.join(bl[i].split(":")[1:])]
            i += 1
        return [False, None, None]
    if listtype == "wl":
        for entry in wl:
            if entry.lower() in line.lower():
                return True
        return False
    if listtype == "sl":
        i=0
        while i < len(sl):  #can be omptimized with for statement
            if re.search(".", sl[i]) != None:
                stringline = sl[i].split(":")[1]
                stringline = stringline.split(" ")
                for everyexpr in stringline:
                    if everyexpr in line:
                        if re.search(".", everyexpr.lower()) != None:
                            newline = line.lower().replace(everyexpr.lower(), sl[i].lower().split(":")[0])
                            blslcheck = searchlist(newline.lower(), "bl")
                            if blslcheck[0] and re.search(".", everyexpr) != None:
                                wlcheck = searchlist(newline, "wl")
                                if not wlcheck:
                                    return [False, 'Used '+everyexpr.lower()+ ' instead of '+sl[i][0]+' attempting to skip filter: '+blslcheck[1],blslcheck[2]]
                                else:
                                    return [True, None, None]
            i = i+1
        matchnum = 0
        for eachline in sl:
            if eachline == "":
                continue
            splitline = eachline.split(": ")[1]
            splitline = splitline.split(" ")
            for entry in splitline:
                if entry in line:
                    if not re.search('[a-z]|[A-Z]|[0-9]',entry) == None:
                        continue
                    matchnum += 1
        if matchnum > 1:
            return [False, 'Attempting to skip filters using multiple similiar charecters','LOW_CONFIDENCE,NOTE(Multiple characters like ν and ә can be contained in the same phrase, this rule detects when one or more occurs)']
        return True

def checkUser(user,waittilledit,noEdit):
    bltest = searchlist(user, "bl")
    try:
        line = str(bltest[1])
    except:
        trace = traceback.format_exc() # Traceback.
        print trace  # Print.
        return
    flags = str(bltest[2])
    if bltest[0]:
        if searchlist(user, "wl"):
            return
        elif noEdit:
            print'No edit - 1' + str(bltest[1]) +" "+ str(bltest[2])
            return 
        else: post(user,str(bltest[1]),str(bltest[2]),str(waittilledit))
    if "NO_SIM_MATCH" in flags:
        return
    slcheck = searchlist(user, "sl")
    if slcheck == True:
        a=1
    elif waittilledit != False and 'WAIT_TILL_EDIT' in str(slcheck[2]):
        waittilledit = True
    try:
        if not slcheck[0] and not bltest[0]:
            if noEdit:
                print "No edit - 2 "+str(slcheck[1]) +" "+ str(slcheck[2])
                return
            return post(user,str(slcheck[1]),str(slcheck[2]),str(waittilledit))
    except:
        if not slcheck and not bltest[0]:
            if noEdit:
                print "No edit - 3"+str(slcheck[1]) +" "+ str(slcheck[2])
                return
            return post(user,str(slcheck[1]),str(slcheck[2]),str(waittilledit))
    return


def main():
    params = {'action': 'query',
        'list': 'logevents',
        'letype': 'newusers',
        'leend':checkLastRun(),
        'lelimit':'5000',
        'leprop':'user',
        'format':'json'
            }
    req = api.Request(site=site, **params)
    result = req.submit()
    reg = result["query"]["logevents"]
    postCurrentRun()
    for entry in reg:
        try:user = entry["user"]
        except KeyError:
            #Placeholder for OS'd users
            oversighted=True
            continue
        if user == "":continue
        checkUser(user, True, False)


def runDry():
    params = {'action': 'query',
        'list': 'logevents',
        'letype': 'newusers',
        'leend':checkLastRun(),
        'lelimit':'5000',
        'leprop':'user',
        'format':'json'
            }
    req = api.Request(site=site, **params)
    result = req.submit()
    reg = result["query"]["logevents"]
    for entry in reg:
        user = entry["user"]
        if user == "":continue
        checkUser(user, True, True)
def post(user, match, flags, restrict):
    summary = "[[User:"+localconfig.botname+"|"+localconfig.botname+"]] "+ localconfig.primarytaskname +" - [[User:"+user+"]] ([[Special:Block/"+user+"|Block]])"
    pagename = localconfig.postpage
    page = pywikibot.Page(site, pagename)
    pagetxt = page.get()
    if user in pagetxt:
        return
    text = "\n\n*{{user-uaa|1="+user+"}}\n"
    if "LOW_CONFIDENCE" in flags:
        text = text + "*:{{clerknote}} There is low confidence in this filter test, please be careful in blocking. ~~~~\n"
    if "WAIT_TILL_EDIT" in flags and restrict != False:#If waittilledit override it not active, aka first run
        edited = getEditCount(user)
        if edited == None:
                return#Skip user, probally non-existant
        if edited == False:
                waitTillEdit(user)#Wait till edit, user has not edited
                return#leave this indented, or it will not continue to report edited users
    if "LABEL" in flags:
        note = flags.split("LABEL(")[1].split(")")[0]
        text = text + "*:Matched: " + note + " ~~~~\n"
    else:
        text = text + "*:Matched: " + match + " ~~~~\n"
    if "NOTE" in flags:
        note = flags.split("NOTE(")[1].split(")")[0]
        text = text + "*:{{clerknote}} " + note + " ~~~~\n"
    if "SOCK_PUPPET" in flags:
        sock = flags.split("SOCK_PUPPET(")[1].split(")")[0]
        text = text + "*:{{clerknote}} Consider reporting to [[WP:SPI]] as [[User:%s]]. ~~~~\n" % sock
    if restrict == False:text + "*:{{done|Waited until user edited to post.}} ~~~~\n"
    if not checkBlocked(user):page.put(pagetxt + text, comment=summary)
def waitTillEdit(user):
    if checkRegisterTime(user, 7):
        checkUser(user, False, True)
        return
    summary = "[[User:DeltaQuadBot|DeltaQuadBot]] Task UAA listing - Waiting for [[User:"+user+"]] ([[Special:Block/"+user+"|Block]]) to edit"
    pagename = localconfig.waitlist
    page = pywikibot.Page(site, pagename)
    pagetxt = page.get()
    text = "\n*{{User|" + user+"}}"
    if text in pagetxt:
        return
    page.put(pagetxt + text, comment=summary)
def checkLastRun():
    pagename = localconfig.timepage
    page = pywikibot.Page(site, pagename)
    time = page.get()
    return time
def postCurrentRun():
    summary = localconfig.editsumtime
    pagename = localconfig.timepage
    page = pywikibot.Page(site, pagename)
    page.put(str(currentTime()), comment=summary)
def cutup(array):
    i=1
    while i < len(array)-1:
        try:
            while array[i][0] != ";":
                i=i+1
            array[i] = array[i].split(":")
            i = i + 1
        except:
            return array
        return array
def getlist(req):
    if req == "bl":
        pagename = localconfig.blacklist
    if req == "wl":
        pagename = localconfig.whitelist
    if req == "sl":
        pagename = localconfig.simlist
    page = pywikibot.Page(site, pagename)
    templist = page.get()
    templist = templist.replace("{{cot|List}}\n","")
    templist = templist.replace("{{cot}}\n","")
    templist = templist.replace("{{cob}}","")
    if req != "wl":templist = templist.replace("\n","")
    if req != "wl":templist = templist.split(";")
    if req == "wl":templist = templist.split("\n;")
    templistarray = cutup(templist)
    return templistarray
def startAllowed(override):
    if override:return True
    pagename = localconfig.gopage
    page = pywikibot.Page(site, pagename)
    start = page.get()
    if start == "Run":
        return True
    if start == "Dry run":
        runDry()
    if start == "Dry":
        print "Notice - Running Checkwait.py only"
        import checkwait #import as it's a py file
        return False
    else:
        return False
def checkWait():
    newlist=""#blank variable for later
    pagename = localconfig.waitlist
    page = pywikibot.Page(site, pagename)
    waiters = page.get()
    waiters = waiters.replace("}}","")
    waiters = waiters.replace("*{{User|","")
    waiters = waiters.split("\n")
    for waiter in waiters:
        if waiter == "":
            continue#Non-existant user
        if checkRegisterTime(waiter, 7):
            continue
        if checkBlocked(waiter):
            continue#If user is blocked, skip putting them back on the list.
        if getEditCount(waiter) == True:#If edited, send them to UAA
            checkUser(waiter,False,False)
            continue
        if waiter in newlist:continue#If user already in the list, in case duplicates run over
        #Continue if none of the other checks have issues with the conditions for staying on the waitlist
        newlist = newlist + "\n*{{User|" + waiter + "}}"
        #print "\n*{{User|" + waiter + "}}"
    summary = localconfig.editsumwait
    pagename = localconfig.waitlist
    page = pywikibot.Page(site, pagename)
    pagetxt = page.get()
    newlist.replace("\n*{{User|}}","")
    page.put(newlist, comment=summary)
global bl
bl = getlist("bl")
global wl
wl = getlist("wl")
global sl
sl = getlist("sl")
if __name__ == '__main__':
    checkUser("Bennentthebastard",False,False)
