#!/usr/bin/env python

import math
import numpy
from pyami import mrc
from scipy import ndimage
from appionlib.apImage import imagefile

def int_to_Hilbert( i, nD=2 ):  # Default is the 2D Hilbert walk.
	index_chunks = unpack_index( i, nD )
	nChunks = len( index_chunks )
	mask = 2 ** nD - 1
	start, end = initial_start_end( nChunks, nD )
	coord_chunks = [0] * nChunks
	for j in range( nChunks ):
		i = index_chunks[ j ]
		coord_chunks[ j ] = gray_encode_travel( start, end, mask, i )
		start, end = child_start_end( start, end, mask, i )
	return pack_coords( coord_chunks, nD )

def Hilbert_to_int( coords ):
	nD = len( coords )
	coord_chunks = unpack_coords( coords )
	nChunks = len( coord_chunks )
	mask = 2 ** nD - 1
	start, end = initial_start_end( nChunks, nD )
	index_chunks = [0] * nChunks
	for j in range( nChunks ):
		i = gray_decode_travel( start, end, mask, coord_chunks[ j ] )
		index_chunks[ j ] = i
		start, end = child_start_end( start, end, mask, i )
	return pack_index( index_chunks, nD )

def initial_start_end( nChunks, nD ):
	# This orients the largest cube so that
	# its start is the origin (0 corner), and
	# the first step is along the x axis, regardless of nD and nChunks:
	return 0,  2**( ( -nChunks - 1 ) % nD )  # in Python 0 <=  a % b  < b.

# Unpacking arguments and packing results of int <-> Hilbert functions.
# nD == # of dimensions.
# A "chunk" is an nD-bit int (or Python long, aka bignum).
# Lists of chunks are highest-order first.
# Bits within "coord chunks" are x highest-order, y next, etc.,
# i.e., the same order as coordinates input to Hilbert_to_int()
# and output from int_to_Hilbert().

def unpack_index( i, nD ):
	p = 2**nD	 # Chunks are like digits in base 2**nD.
	nChunks = max( 1, int( math.ceil( math.log( i + 1, p ) ) ) ) #   # of digits
	chunks = [ 0 ] * nChunks
	for j in range( nChunks - 1, -1, -1 ):
		chunks[ j ] = i % p
		i /= p
	return chunks

def pack_index( chunks, nD ):
	p = 2**nD  # Turn digits mod 2**nD back into a single number:
	return reduce( lambda n, chunk: n * p + chunk, chunks )

def unpack_coords( coords ):
	biggest = reduce( max, coords )  # the max of all coords
	nChunks = max( 1, int( math.ceil( math.log( biggest + 1, 2 ) ) ) ) # max # of bits
	return transpose_bits( coords, nChunks )

def pack_coords( chunks, nD ):
	return transpose_bits( chunks, nD )

## transpose_bits --
#	Given nSrcs source ints each nDests bits long,
#	return nDests ints each nSrcs bits long.
#	Like a matrix transpose where ints are rows and bits are columns.
#	Earlier srcs become higher bits in dests;
#	earlier dests come from higher bits of srcs.
def transpose_bits( srcs, nDests ):
	srcs = list( srcs )  # Make a copy we can modify safely.
	nSrcs = len( srcs )
	dests = [ 0 ] * nDests
	# Break srcs down least-significant bit first, shifting down:
	for j in range( nDests - 1, -1, -1 ):
		# Put dests together most-significant first, shifting up:
		dest = 0
		for k in range( nSrcs ):
			dest = dest * 2 + srcs[ k ] % 2
			srcs[ k ] /= 2
		dests[ j ] = dest
	return dests

# Gray encoder and decoder from http://en.wikipedia.org/wiki/Gray_code
def gray_encode( bn ):
	assert bn >= 0
	assert type( bn ) in [ int, long ]
	return bn ^ ( bn / 2 )

def gray_decode( n ):
	sh = 1
	while True:
		div = n >> sh
		n ^= div
		if div <= 1: return n
		sh <<= 1

def gray_encode_travel( start, end, mask, i ):
	travel_bit = start ^ end
	modulus = mask + 1		  # == 2**nBits
	# travel_bit = 2**p, the bit we want to travel.
	# Canonical Gray code travels the top bit, 2**(nBits-1).
	# So we need to rotate by ( p - (nBits-1) ) == (p + 1) mod nBits.
	# We rotate by multiplying and dividing by powers of two:
	g = gray_encode( i ) * ( travel_bit * 2 )
	return ( ( g | ( g / modulus ) ) & mask ) ^ start

def gray_decode_travel( start, end, mask, g ):
	travel_bit = start ^ end
	modulus = mask + 1		  # == 2**nBits
	rg = ( g ^ start ) * ( modulus / ( travel_bit * 2 ) )
	return gray_decode( ( rg | ( rg / modulus ) ) & mask )

def child_start_end( parent_start, parent_end, mask, i ):
	start_i = max( 0, ( i - 1 ) & ~1 )  # next lower even number, or 0
	end_i =   min( mask, ( i + 1 ) |  1 )  # next higher odd number, or mask
	child_start = gray_encode_travel( parent_start, parent_end, mask, start_i )
	child_end   = gray_encode_travel( parent_start, parent_end, mask, end_i )
	return child_start, child_end

if __name__ == "__main__":
	dim = 8 #powers of two
	maxdim = dim*2+1
	print("maxdim=", maxdim)
	#maxdim += 4
	hilb = numpy.zeros((maxdim,maxdim,maxdim))
	lastcoord = None
	for i in range(dim**3):
		coord = 2*numpy.array(int_to_Hilbert(i, 3))
		hilb[coord[0]+1, coord[1]+1, coord[2]+1] = 1
		if lastcoord is not None:
			lastcoord = (coord + lastcoord)/2
			hilb[lastcoord[0]+1, lastcoord[1]+1, lastcoord[2]+1] = 1
		lastcoord = coord
	maxdim = max(hilb.shape)

	scalefactor = math.floor(math.log(800./(2*dim+2))/math.log(2.))

	scale = 2**scalefactor
	print(dim, scale)

	hilb = ndimage.zoom(hilb, (scale, 1, scale), order=0)
	name = "hilbert%d"%(dim)
	#mrc.write(hilb, name+".mrc")

	step = int(scale*2)+4
	for xy in range(1, maxdim//2):
		hilb[xy*step,:,:] = 0.5
		hilb[:,:,xy*step] = 0.5

	for j in range(1, maxdim-1):
		image = 1 - hilb[:,j,:]
		name = "hilbert%d-%03d.png"%(dim, j)
		imagefile.arrayToPng(image, name)
