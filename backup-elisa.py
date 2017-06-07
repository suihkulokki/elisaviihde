# Elisa Viihde API Python implementation usage demo

import getopt, sys, getpass, elisaviihde, os, re, keyring
from subprocess import call

def main():
  # Parse command line args
  if len(sys.argv[1:]) < 2:
    print "ERROR: Usage:", sys.argv[0], "[-u username]" 
    sys.exit(2)
  try:
    opts, args = getopt.getopt(sys.argv[1:], "u:v", ["username"])
  except getopt.GetoptError as err:
    print "ERROR:", str(err)
    sys.exit(2) 
  
  # Init args
  username = ""
  verbose = False
  
  # Read arg data
  for o, a in opts:
    if o == "-v":
      verbose = True
    elif o in ("-u", "--username"):
      username = a
    else:
      assert False, "unhandled option"
  
  password = keyring.get_password("elisaviihde", username)
  if password is None:
      # Ask password securely on command line
      password = getpass.getpass('Password: ')
      keyring.set_password("elisaviihde", username, password)

    
  # Init elisa session
  try:
    elisa = elisaviihde.elisaviihde(verbose)
  except Exception as exp:
    print "ERROR: Could not create elisa session"
    sys.exit(1)
    
  # Login
  try:
    elisa.login(username, password)
  except Exception as exp:
    print "ERROR: Login failed, check username and password"
    sys.exit(1)
    
  allfolders = elisa.getallfolders()
  
  if verbose:
    for folder in allfolders: print folder["name"]
    
  allrecordings = elisa.getallrecordings()
  print str(len(allrecordings)) + " recordings total."

  totaltime = 0
  for rec in allrecordings:
    totaltime += rec["duration"]
    try:
      kausi = None
      if "Kausi" in rec["description"] or "kausi" in rec["description"]:
        m = re.search("[Kk]ausi ?([0-9]+)", rec["description"])
        if m:
          kausi = m.group(1)
        else:
          m = re.search("([0-9]+)\. ?[kK]ausi", rec["description"])
          if m:
            kausi = m.group(1)
          else:
            m = re.search("([0-9]+)\. ?[tT]uotantokausi", rec["description"])
            if m:
              kausi = m.group(1)
            else:
              print rec["description"] 
      if kausi>8:
        print rec["description"]
      
      jakso = None
      if "/" in rec["description"]:
        m = re.search("([0-9]+)/([0-9]+)", rec["description"])
        if m:
          jakso = m.group(1);
          print jakso;
        else:
          print rec["description"]

      if "akso" in rec["description"]:
        print rec["description"]
          
    except KeyError:
      continue
    
  print "Total duration " + str(totaltime) + " sec (" + str(totaltime/60) + " min = " + str(totaltime/3600) + " hr)"
  
  # # Read and print recording folders
  # folders = elisa.getfolders()
  
  # print "\nFound folders:"
  # for folder in folders:
  #   print str(folder["id"]) + ": " + folder["name"]
  
  # # Read and print recording folders
  # folderid = folders[0]["id"]
  # recordings = elisa.getrecordings(folderid)
  
  # print "\nFound recordings from folder " + str(folderid) + ":"
  # for recording in recordings:
  #   print str(recording["programId"]) + ": " + recording["name"] + " (" + recording["startTimeFormatted"] + ")"
  
  # # Get recording stream uri from first recording
  # programid = recordings[0]["programId"]
  # streamuri = elisa.getstreamuri(programid)
  
  # print "\nFound stream uri from recording " + str(programid) + ":"
  # print streamuri
  
  # callstr = 'ffmpeg -i "' + streamuri + '" -c:v libx264 -preset medium -crf 20 -c:a copy -sn "' + recordings[0]["name"] + '.mkv"'

  # print callstr
  #os.system(callstr)
#  call(callstr, shell=True)
  
  # Close session
  elisa.close()

if __name__ == "__main__":
  main()

