#!/usr/bin/python
import getopt, sys, getpass, elisaviihde, os, re, keyring
import cPickle as pickle
from subprocess import call
from time import sleep

def main():
  # Parse command line args
  if len(sys.argv[1:]) < 4:
    print "ERROR: Usage:", sys.argv[0], "[-u username -l listfile]"
    print "        -s burn subtitles -2 alternative burn subtitles"
    print "        -d debug -o only download"
    sys.exit(2)
  try:
    opts, args = getopt.getopt(sys.argv[1:], "d2osu:l:", ["username"])
  except getopt.GetoptError as err:
    print "ERROR:", str(err)
    sys.exit(2)

  # Init args
  username = ""
  listfile = None
  verbose = False

  datadir = os.path.dirname(os.path.realpath(__file__))
  download_only = False
  debug = False
  subtitles = False
  subtitles2 = False

  # Read arg data
  for o, a in opts:
    if o == "-l":
      listfile = a
    elif o in ("-u", "--username"):
      username = a
    elif o == "-d":
      debug = True
    elif o == "-o":
      download_only = True
    elif o == "-s":
      subtitles = True
    elif o == "-2":
      subtitles2 = True
    else:
      assert False, "unhandled option"

  if username=="" or not listfile:
    print "ERROR: username or programId missing"
    sys.exit(2)

  try:
    input = open(listfile,"r")
  except Exception as err:
    print "ERROR: Opening listfile failed, " + str(err)

  with open(datadir + "/recording_data.pkl", "rb") as input_data:
    allrecordings = pickle.load(input_data)

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
  for text in input:

    # Login
    for i in range(10):
      try:
        elisa.login(username, password)
        break
      except Exception as exp:
        print "WARNING: Login failed, retrying after one minute"
        sleep(60)
    else:
      print "ERROR: Login failed 10 times in row, exiting"
      sys.exit(1)

    match = re.match('^(\d+)\: (.+)\: (\d+:\d+:\d+)',text)

    if not match:
        match = re.match('^(\d+)\: (.+)',text)
        if not match:
            continue;

    if debug: print match.group(1) + " " + match.group(2)

    programId = match.group(1)
    outfilename = match.group(2).decode("utf8")

    try:
      prog = next(x for x in allrecordings if x["programId"]==int(programId))
    except StopIteration as exp:
      print str(programId) + ": " + outfilename + " not found in database"
      continue

    print "Processing " + programId + ", " + prog["name"]

    try:
      streamuri = elisa.getstreamuri(programId)
    except Exception as exp:
      print "WARNING: Stream not found, skipping"
      continue

    if download_only:
      wget_command = [ "wget", streamuri, "-O", outfilename + ".ts" ]
      print "Starting download: " + " ".join(wget_command)
      try:
        returncode = call(wget_command)
      except KeyboardInterrupt as exp:
        print "Interrupted from keyboard, exiting"
        os.remove(outfilename+".mkv")
        exit(0)
      continue

    ffmpeg_command = [ "ffmpeg"]
    if len(match.groups()) == 3:
        ffmpeg_command +=  [ "-ss", match.group(3) ]
    ffmpeg_command += [ "-i", streamuri ]

    if subtitles:
        ffmpeg_command += [ '-filter_complex', "[0:v][0:s]overlay" ]
    if subtitles2:
        ffmpeg_command += [ '-filter_complex', "[0:v][0:4]overlay" ]
    if not debug:
        ffmpeg_command += [ '-loglevel', 'fatal' ]

    # input stream and codec options
    ffmpeg_command += ['-c:v', 'libx264', '-preset', 'medium', '-crf','22',
            '-c:a', 'aac', '-strict', 'experimental', '-sn',
            '-metadata', 'description=' + prog["description"],
            '-metadata', 'title='+ outfilename,
            outfilename + '.mkv'
            ]
    print "Starting encoding: " + " ".join(ffmpeg_command)

    try:
        returncode = call(ffmpeg_command)
    except KeyboardInterrupt as exp:
      print "Interrupted from keyboard, exiting"
      os.remove(outfilename+".mkv")
      exit(0)

    if returncode:
      print "=================== WARNING: Possible ffmpeg failure, returncode " + str(returncode)

    # Close session (new one opened for each file)
    try:
      elisa.close()
    except Exception as exp:
      print "Closing connection failed. Will continue anyway."
      continue

    # All files downloaded

if __name__ == "__main__":
  main()

