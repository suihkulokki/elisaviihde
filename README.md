Elisa Viihde Backup tool
=====

Usage example:
-----
Download your elisaviihde folders and recordings info:
```
$ ./elisa-dump-program-info.py -u "username"
```
Find the folder id you want to back up
```
$ ./elisa-show-folder-dump.py
...
3140525: Kauniit ja Rohkeat (61 recordings)
...
```
Make a batch download list of the folder to download
```
$ ./elisa-show-program-dump.py -f 3140525 -o kauniit.list
```
The generated list is in form of "programid: filename".  
Start batch download:

```
./elisa-download-list.py -u "username" -l ../kauniit.list
```

Use the -s or -2 options to record YLE subtitles.





