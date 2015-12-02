#!/usr/bin/python
import struct
import scipy
import wave
import os
import sys, time

blocksize = int(sys.argv[1])
inputfile = sys.argv[2]
outputfile = sys.argv[3]
channels = 2

if inputfile[-9:] != '.tar.lzma':
	zippercommand = 'lzma -d -c < '+inputfile+'.tar.lzma'+' | tar -xf -'
else:
	zippercommand = 'lzma -d -c < '+inputfile+' | tar -xf -'
	inputfile = inputfile[:-9]
os.system(zippercommand)
time.sleep(1)

def read_lutable():
	f = open(inputfile+'_lutable.bin', "rb")
	lutable = scipy.array([])
	condition = 1
	while condition:
		s = f.read(4)
		if not s:
			lutable = scipy.reshape(lutable,(-1,blocksize))
			break
		else:
			entry = struct.unpack('>i',s)
			lutable = scipy.append(lutable, entry)
	f.close()
	os.system('rm '+inputfile+'_lutable.bin')
	return lutable

def read_index():
	f = open(inputfile+'_index.bin','rb')
	indexlength = f.read()
	indexlength = len(indexlength) / struct.calcsize('>H')
	index = scipy.zeros(indexlength)
	f.seek(0)
	condition = 1
	counter = 0
	while condition:
		s = f.read(2)
		if not s:
			break
		else:
			entry = struct.unpack('>H',s)
			index[counter] = entry[0]
		counter += 1
	f.close()
	os.system('rm '+inputfile+'_index.bin')
	return index


lutable = read_lutable()
index = read_index()

output = scipy.zeros(len(index)*blocksize,dtype=int)
print "Generating wav..."
counter = 0
for k in index:
	output[counter*blocksize:counter*blocksize+blocksize] = lutable[k]
	counter +=1

output = scipy.reshape(output.astype(int),(-1,channels))
wavfilename = outputfile
wav_file = wave.open(wavfilename,'wb')
nchannels = 2
sampwidth = 2
framerate = 44100
comptype = "NONE"
compname = "not compressed"
wav_file.setparams((nchannels,sampwidth,framerate,'',comptype,compname))

print "Writing wav to disk..."
for s in output:
	wav_file.writeframesraw(struct.pack('2h',s[0],s[1]))
wav_file.close()
