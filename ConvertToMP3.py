#!/usr/bin/python
#
#    Copyright (C) Brad Smith 2008
#
#    This file is ConvertToMP3
#
#    ConvertToMP3 is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    ConvertToMP3 is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
#
# A script to convert non-DRM'd iTunes M4A files to MP3 so they will
# play with portable players that don't support M4A.
#
# Must install id3v2, mplayer, lame, python-mutagen

import commands, subprocess, os, sys
from mutagen.mp4 import MP4, MP4StreamInfoError

def getTag(tagInfo, primaryTag, secondaryTag = u""):
	tagData = u""
	if tagInfo.tags.has_key(primaryTag):
		tagData = tagInfo.tags[primaryTag]
	elif secondaryTag != u"" and tagInfo.tags.has_key(secondaryTag):
		tagData = tagInfo.tags[secondaryTag]

	while type(tagData) == list or type(tagData) == tuple:
		tagData = tagData[0]
	
	if type(tagData) != unicode:
		tagData = str(tagData)
	return tagData


errstrings = []

if len(sys.argv) == 1:
	print "ERROR: This program must be run with the name of the directory containing the M4A files as the first argument.\n"
	print "Examples:"
	print "\t./ConvertToMP3.py /home/username/my_music"
	print "\t./ConvertToMP3.py /media/music /tmp/destination"
	sys.exit(1)

convertdir = unicode(os.path.abspath(sys.argv[1]), 'UTF-8')
print ("Attempting to convert M4A files in '" + convertdir + "'").encode('UTF-8')
if not os.path.isdir(convertdir):
	print "ERROR: The argument '" + convertdir + "' is not a directory."
	sys.exit(2)

m4as = []
for current, dirs, files in os.walk(convertdir, True):
	for f in files:
		if f.lower().endswith(".m4a"):
			m4as.append(os.path.join(convertdir, current, f))

if len(m4as) == 0 or (len(m4as) == 1 and m4as[0] == u''):
	print "ERROR: No M4A files were found in the specified directory."
	sys.exit(3)

destdir = os.path.normpath(convertdir) + u"_mp3"
if len(sys.argv) == 3:
	destdir = unicode(os.path.abspath(sys.argv[2]), 'UTF-8')
if os.path.isdir(destdir):
	print ("ERROR: The destination directory '" + destdir + "' already exists. Please delete or rename this directory before running this program.").encode('UTF-8')
	sys.exit(4)
print ("Converted MP3 files will be placed in '" + destdir + "'").encode('UTF-8')

os.makedirs(destdir)

convertdict = {}
for m4a in m4as:
	sourcem4a = os.path.normpath(os.path.join(convertdir, m4a))
	srcprefix = os.path.commonprefix([convertdir, sourcem4a])
	m4apostfix = m4a[len(srcprefix):]
	destm4a = os.path.normpath(destdir + m4apostfix)[:-4] + u'.mp3'
	convertdict[sourcem4a] = destm4a

wav = u'/tmp/converttomp3_outfile.wav'
for src in convertdict.keys():
	if not os.path.isfile(src):
		print ("ERROR: The file '" + src + "' does not exist. This should never happen; there must be an error in the program. Sorry :)").encode('UTF-8')
		sys.exit(5)

	dest = convertdict[src]
	if not os.path.isdir(os.path.split(dest)[0]):
		os.makedirs(os.path.split(dest)[0])

	title = artist = album = track = genre = ""
	try:
		tagInfo = MP4(src)
		title = getTag(tagInfo, '\xa9nam')
		artist = getTag(tagInfo, '\xa9ART', 'aART')
		album = getTag(tagInfo, '\xa9alb')
		track = getTag(tagInfo, 'trkn')
		genre = getTag(tagInfo, '\xa9gen')

	except MP4StreamInfoError:
		errstrings.append("ERROR: The file '" + src + "' seems to have invalid song information tags. Unfortunately, this means that the resulting MP3 file will not have embedded tags.")

	try:
		subprocess.check_call([u'mplayer', u'-quiet', u'-ao', u'pcm', src, u'-ao', u'pcm:file=' + wav])
	except subprocess.CalledProcessError:
		errstrings.append("ERROR: The file '" + src + "' could not be converted to a WAV with mplayer. The file may be corrupt.")
		continue
	
	try:
		subprocess.check_call([u'lame', u'--quiet', u'-h', u'-b', u'192', wav, dest])
	except subprocess.CalledProcessError:
		errstrings.append("ERROR: The file '" + src + "' could not be converted to an MP3 with lame. An error has occurred.")
		continue

	if title != "":
		subprocess.check_call([u'id3v2', u'-t', title, dest])
	if artist != "":
		subprocess.check_call([u'id3v2', u'-a', artist, dest])
	if album != "":
		subprocess.check_call([u'id3v2', u'-A', album, dest])
	if track != "":
		subprocess.check_call([u'id3v2', u'-T', track, dest])
	if genre != "":
		subprocess.check_call([u'id3v2', u'-g', genre, dest])


if os.path.isfile(wav):
	os.remove(wav)

print "\n\n**************************************************************************\n\n"
print ("MP3 files were created in the '" + destdir + "' directory.").encode('UTF-8')
if len(errstrings) == 0:
	print "Conversion succeeded! No errors occurred."
else:
	print "The following errors took place during conversion:"
	for err in errstrings:
		print err.encode('UTF-8')