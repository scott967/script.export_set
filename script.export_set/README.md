
# Export movie sets to set.nfo

Kodi program addon to export video library set/collection info to set.nfo
files in user's MSIF (Movie Set Info Folder).

Run from Kodi's program addon list, or via `RunScript(script.export_set)`

You must have a valid MSIF path in Kodi settings Media/Video
The addon will display a Kodi yes/no dialog asking if you want to overwrite
existing set.nfo files (i.e., update all set.nfo files).  **Yes** will update
existng files and add files for new sets or sets that have not been exported
to set.nfo.  **No** will only export set.nfo files for missing set.nfo files
in the MSIF.  Note that in either case new set/collection subfolders
(with the set.nfo file) will be created in the MSIF if they don't exist when the
addon is run.