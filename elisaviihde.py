# Elisa Viihde API Python implementation
# License: GPLv3
# Author: enyone
# Version: 1.4
# https://github.com/enyone/elisaviihde

import requests, json, re, time, datetime, math
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class elisaviihde:
  # Init args
  verbose = False
  baseurl = "https://elisaviihde.fi"
  apiurl = "https://api.elisaviihde.fi"
  ssobaseurl = "https://id.elisa.fi"
  session = None
  authcode = None
  userinfo = None
  inited = False
  verifycerts = False
  
  def __init__(self, verbose=False):
    #    urllib3.disable_warnings()
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # Init session to store cookies
    self.verbose = verbose
    self.session = requests.Session()
    self.session.headers.update({"Referer": self.baseurl + "/"})
    
    # Make initial request to get session cookie
    if self.verbose: print "Initing session..."
    
    init = self.session.get(self.baseurl + "/", verify=self.verifycerts)
    self.checkrequest(init.status_code)

    # disable warnings for unverified https requests
    
  def login(self, username, password):
    # Login using api.elisaviihde.fi
    loginreq = self.session.post(self.apiurl + "/etvrecorder/login.sl&ajax",
                                 data={"username": username,
                                       "password": password},
                             headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                      "X-Requested-With": "XMLHttpRequest"},
                             verify=self.verifycerts)
    self.checkrequest(loginreq.status_code)
    
    # Login with username and password
    if self.verbose: print "Logging in with username and password..."
    user = self.session.post(self.baseurl + "/api/user",
                             data={"username": username,
                                   "password": password},
                             headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                      "X-Requested-With": "XMLHttpRequest"},
                             verify=self.verifycerts)
    self.checkrequest(user.status_code)
    try:
      self.userinfo = user.json()
    except ValueError as err:
      raise Exception("Could not fetch user information", err)
    self.inited = True
  
  def islogged(self):
    if self.inited:
      return True
    try:
      logincheck = self.session.get(self.baseurl + "/tallenteet/api/folders",
                                    headers={"X-Requested-With": "XMLHttpRequest"},
                                    verify=self.verifycerts)
      self.checkrequest(logincheck.status_code)
      self.inited = True
      return True
    except Exception as err:
      return False
    
  def checklogged(self):
    if not self.islogged():
      raise Exception("Not logged in")
  
  def checkrequest(self, statuscode):
    if not statuscode == requests.codes.ok:
      raise Exception("API request failed with error code: " + str(statuscode))
  
  def close(self):
    if self.verbose: print "Logging out and closing session..."
    logout = self.session.post(self.baseurl + "/api/user/logout",
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.session.close()
    self.userinfo = None
    self.authcode = None
    self.inited = False
    self.checkrequest(logout.status_code)
  
  def gettoken(self):
    return self.authcode
  
  def getuser(self):
    return self.userinfo
  
  def getsession(self):
    return requests.utils.dict_from_cookiejar(self.session.cookies)
    
  def setsession(self, cookies):  
    self.session.cookies=requests.utils.cookiejar_from_dict(cookies)
  
  def walk(self, tree, parent=None):
    # Walk folder tree recursively
    flat = []
    subtree = None
    if "folders" in tree:
      if len(tree["folders"]) > 0:
        subtree = tree["folders"]
      del tree["folders"]
    if "id" in tree:
      tree["parentFolder"] = parent if tree["id"] > 0 else None
      flat.append(tree)
    if subtree:
      for folder in subtree:
        flat += self.walk(folder, (tree["id"] if "id" in tree else 0))
    return flat
  
  def getfolders(self, folderid=0):
    # Get folders
    if self.verbose: print "Getting folders..."
    self.checklogged()
    folders = self.session.get(self.baseurl + "/tallenteet/api/folders",
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.checkrequest(folders.status_code)
    return [folder for folder in self.walk(folders.json()) if folder["parentFolder"] == folderid]

  def getallfolders(self):
    self.checklogged()
    folders = self.session.get(self.baseurl + "/tallenteet/api/folders",
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.checkrequest(folders.status_code)
    return [folder for folder in self.walk(folders.json())]
    
  def getfolderstatus(self, folderid=0):
    # Get folder info
    if self.verbose: print "Getting folder info..."
    self.checklogged()
    folder = self.session.get(self.baseurl + "/tallenteet/api/folder/" + str(folderid),
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.checkrequest(folder.status_code)
    return folder.json()

  def getallrecordings(self, sortby="startTime", sortorder="desc", status="all"):
    self.checklogged()
    recordings = []
    allfolders = self.getallfolders()

    for folder in allfolders:
      recordings += self.getrecordings(folder["id"])
    return recordings
    
  def getrecordings(self, folderid=0, page=None, sortby="startTime", sortorder="desc", status="all"):
    # Get recordings from folder
    self.checklogged()
    if self.verbose: print "Getting recordings..."
    recordings = []
    if page == None:
      folder = self.getfolderstatus(folderid)
      # Append rest of pages to list (50 recordings per page)
      maxpage = int(math.floor(folder["recordingsCount"] / 50))
      if maxpage > 0:
        pages = range(0, maxpage+1)
      else:
        pages = [0]
    else:
      pages = [page]
    for pageno in pages:
      recordingspp = self.session.get(self.baseurl + "/tallenteet/api/recordings/" + str(folderid)
                                        + "?page=" + str(pageno)
                                        + "&sortBy=" + str(sortby)
                                        + "&sortOrder=" + str(sortorder)
                                        + "&watchedStatus=" + str(status),
                                      headers={"X-Requested-With": "XMLHttpRequest"},
                                      verify=self.verifycerts)
      self.checkrequest(recordingspp.status_code)
      recordings += recordingspp.json()
    return recordings
  
  def getprogram(self, programid=0):
    # Parse program information
    self.checklogged()
    if self.verbose: print "Getting program info..."
    uridata = self.session.get(self.baseurl + "/ohjelmaopas/ohjelma/" + str(programid), verify=self.verifycerts)
    self.checkrequest(uridata.status_code)
    programname = ""
    programdesc = ""
    programsrvc = ""
    programtime = 0
    try:
      for line in uridata.text.split("\n"):
        if "itemprop=\"name\"" in line and "data-programid" in line:
          programname = re.findall('<h3.*?>(.*?)</h3>', line)[0]
        elif "itemprop=\"description\"" in line:
          programdesc = re.findall('<p.*?>(.*?)</p>', line)[0]
        elif "itemprop=\"name\"" in line:
          programsrvc = re.findall('<p.*?>(.*?)</p>', line)[0]
        elif "itemprop=\"startDate\"" in line:
          programtimestr = re.findall('<span.*?>(.*?)</span>', line)[0]
          programtime = int(datetime.datetime.fromtimestamp(
                              time.mktime(time.strptime(programtimestr,
                                                        "%d.%m.%Y %H:%M"))).strftime("%s"))
          programtime = programtime * 1000
    except Exception as exp:
      print "ERROR:", str(exp)
    except Error as exp:
      print "ERROR:", str(exp)
    
    return {"name": programname, "description": programdesc, "serviceName": programsrvc, "startTimeUTC": programtime}
  
  def getstreamuri(self, programid=0):
    # Parse recording stream uri for program
    self.checklogged()
    if self.verbose: print "Getting stream uri info..."
    uridata = self.session.get("https://api.elisaviihde.fi/etvrecorder/program.sl?programid=" + str(programid) + "&ajax", 
                               verify=self.verifycerts)
    self.checkrequest(uridata.status_code)
    programinfo = uridata.json()
    if programinfo["url"]==None:
      raise Exception("Could not read program URL, log in unsuccessful?")
    return programinfo["url"]

  def markwatched(self, programid=0):
    # Mark recording as watched
    if self.verbose: print "Marking as watched..."
    self.checklogged()
    watched = self.session.get(self.baseurl + "/tallenteet/api/watched/" + str(programid),
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.checkrequest(watched.status_code)

