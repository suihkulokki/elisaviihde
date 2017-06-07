import getopt, sys, getpass, elisaviihde, os, re, keyring
from subprocess import call

def main():
  # Parse command line args
  if len(sys.argv[1:]) < 4:
    print "ERROR: Usage:", sys.argv[0], "[-u username -p id]" 
    sys.exit(2)
  try:
    opts, args = getopt.getopt(sys.argv[1:], "u:p:", ["username"])
  except getopt.GetoptError as err:
    print "ERROR:", str(err)
    sys.exit(2) 
  
  # Init args
  username = ""
  programId = None
  verbose = False
  
  # Read arg data
  for o, a in opts:
    if o == "-p":
      programId = a
    elif o in ("-u", "--username"):
      username = a
    else:
      assert False, "unhandled option"

  if username=="" or not programId:
      print "ERROR: username or programId missing"
      sys.exit(2)
      
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
    
  streamuri = elisa.getstreamuri(programId)

  print "Found stream uri from recording " + str(programId) + ":"
  print streamuri
  
  callstr = 'ffmpeg -i "' + streamuri + '" -c:v libx264 -preset medium -crf 20 -c:a copy -sn "' + 'download.mkv"'

  print callstr

  call(callstr, shell=True)
  
  # Close session
  elisa.close()

if __name__ == "__main__":
  main()

