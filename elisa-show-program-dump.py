#!/usr/bin/python
import re, sys, getopt
import cPickle as pickle

import codecs

def main():
  # parse command line
  folderid = None
  outfile = None
  of = None
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], "f:o:")
  except getopt.GetoptError as err:
    print "ERROR:", str(err)
    sys.exit(2)
    
  for o, a in opts:
    if o == "-f":
      folderid = a
    elif o == "-o":
      outfile = a
    else:
      assert False, "unhandled option"
      
  with open("recording_data.pkl", "rb") as input:
    allrecordings = pickle.load(input)

  if outfile:
    of = codecs.open(outfile, "w", "utf-8")
        
  totaltime = 0
  for rec in allrecordings:
    if folderid:
      if str(rec["folderId"]) <> folderid:
        continue
      
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

      jakso = None
      if "/" in rec["description"]:
        m = re.search("([0-9]+) ?/([0-9]+)", rec["description"])
        if m:
          if m.group(2)>2:
            jakso = m.group(1)
      if "osa" in rec["description"]:
        m = re.search("osa ([0-9]+)", rec["description"])
        if m:
            jakso = m.group(1)

      pv = None
      m = re.search("(\d+)\.(\d+)\.(\d+)", rec["startTime"])
      if m:
          pv = m.group(1)
          kk = m.group(2)
          vvvv = m.group(3)

      name = rec["name"]
      m = re.search("^(Elokuva:|Kino:|#Subleffa:|Kino Klassikko:|E:|Kino Into:|AVA Elokuva:) (.+)", name);
      if m:
        name = m.group(2)
      
      filename = re.sub('\([\dSKT]+\)','',name)
      if kausi and jakso:
        filename += "S" + kausi.zfill(2) + "E" + jakso.zfill(2)
      if not kausi and jakso: filename += "S01E" + jakso.zfill(2) 
#      if pv: filename += "_" + vvvv + kk + pv

#      filename = re.sub(' ','_',filename)
#      filename = re.sub('_+','_',filename)

      # Remove illegal characters ':' '?' and trailing spaces
      filename = re.sub(':', '-', filename)
      filename = re.sub('\?', '', filename)
      filename = re.sub(' +$', '', filename)

      rec["filename"] = filename

      print str(rec["programId"]) + ": " + filename
      print rec["description"]
      
      if of: print >> of,  str(rec["programId"]) + ": " + filename

    except KeyError:
      continue

  if of: of.close()
  
  print "Total duration " + str(totaltime) + " sec (" + str(totaltime/60) + " min = " + str(totaltime/3600) + " hr)"

if __name__ == "__main__":
  main()
