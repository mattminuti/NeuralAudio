#!/usr/bin/python
import multiprocessing as mp
import scipy
import sys
import wave
import struct
from matplotlib import mlab
import os
from scipy.io import wavfile


inputfile = sys.argv[1]
blocksize = int(sys.argv[2])
errortolerance = int(sys.argv[3])
outputfile = sys.argv[4]
channels = 2
#load the wavefile
(samplerate, data) = scipy.io.wavfile.read(inputfile)
neededzeros = blocksize-(len(data)%blocksize)
data = scipy.append(data,scipy.zeros((channels,neededzeros)))
data = scipy.reshape(data,(-1,blocksize))
original_data = data

lutable = scipy.array([], dtype=int)
q = scipy.array([], dtype=int)
#finds which entries are within the percent error tolerance to the reference
while data.shape[0] != 0:
	print "Generating lutable, " + str(len(data))
	q = (data-data[0,:])**2
	q_sum = scipy.sum(q,1)
	q_n = scipy.sqrt(q_sum)
	q_d = scipy.sqrt(scipy.sum(data[0,:]**2,0))
	if scipy.all(data[0,:] == 0): #to avoid division by zero on an allzero block
		print "This is a zero case"
		lutable = scipy.append(lutable,data[0,:]) #add it to the lookup table
		results = scipy.all(data == scipy.zeros(data.shape),1) #locate the allzero blocks
		data = data[results == False] #eliminate the matches
	else:
		q = q_n / q_d * 100 
		results = q < errortolerance
		lutable = scipy.append(lutable,data[0,:])
		data = data[results == False]
lutable = scipy.reshape(lutable.astype(int),(-1,blocksize))

#isolate any zeros in the lookup table for easy reference later.
#we do this by checking where all entries in a block are equal to zero
lutable_zero_index = mlab.find(scipy.all(lutable==0,1))

#defining the parallel computation thingies
def matchfinder(stuff):
	i,k = stuff
	q = (k - lutable)**2
	q_sum = scipy.sum(q,1)
	q_n = scipy.sqrt(q_sum)
	q_d = scipy.sqrt(sum(k**2,0))
	if scipy.all(k ==0):
		return (i, lutable_zero_index)
	else:
		q = q_n / q_d * 100
		return (i, scipy.argmin(q))

data = original_data
index = scipy.zeros(len(data))

if __name__ == '__main__':
    p = mp.Pool()
    res = p.map_async(matchfinder, list(enumerate(data)), 1)
    p.close()
    p.join()
    results = res.get()
    for i,s in results:
    	index[i] = s

indexfilename = outputfile + "_index.bin"
file = open(indexfilename,'wb')
for s in index:
	indexdata = struct.pack('>H',s)
	file.write(indexdata)
file.close()

lutable = scipy.reshape(lutable.astype(int),(1,-1))
lutable = lutable[0]
lutablefilename = outputfile + "_lutable.bin"
file = open(lutablefilename,'wb')
for s in lutable:
	ludata = struct.pack('>i',s)
	file.write(ludata)
file.close()

zippercommand = 'tar -cf - ' + outputfile + '*.bin | lzma -c > ' + outputfile+'.tar.lzma'
os.system(zippercommand)

cleanupcommand = 'rm '+indexfilename+' '+lutablefilename
os.system(cleanupcommand)



#for testing, also generate a wav from the output
if sys.argv[5][-4:] == ".wav":
	wavfilename = sys.argv[5]
	lutable = scipy.reshape(lutable,(-1,blocksize))
	for i,s in results:
		index[i] = s
	indexlength = len(index)
	output = scipy.zeros(indexlength*blocksize, dtype=int)
	print "Generating wav..."
	counter = 0
	for k in index:
		output[counter*blocksize:counter*blocksize+blocksize] = lutable[k]
		counter += 1

	output = scipy.reshape(output.astype(int),(-1,channels))
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
