from random import randint,getrandbits
from math import log,ceil



def h(p, g, k, x, y):
	#print("woah",x,y)
	y = int(y,2)

	assert(x<p and y<p)
	return (pow(g,x,p)*pow(g,y,p))%p


def MerkleDamgard(p, g, k, x, l):
	l = 2*(l-1) - l
	L = len(x)
	B = int(L/l)
	rem = L%l 
	# pad with zero to make it a multiple of l
	x += "0"*((B+1)*l - rem)
	B += 1

	# binL = bin(L)[2:]
	# rem = l - len(binL)

	z = p-1
	for i in range(1,B+1):
		xi = x[(i-1)*l:i*l]
		z = h(p, g, k, z, xi)
		#print("result ",z)


	return z


def Hash(p, g, k, t, m):
	ms = bin(t)[2:] + bin(m)[2:]
	l = int(log(p,2))+1
	z = MerkleDamgard(p, g, k, ms, l)
	
	#print("Final Hash ",int(z))
	return int(z)


def Gen(p, g):
	x = randint(1,p-1)
	k = randint(1,p-1)
	return (x, pow(g,x,p), k)

def Sign(p, g, m):
	x,y,k = Gen(p,g)
	#print("x y k",x,y,k)
	r = randint(1,p-1)
	t = pow(g,r,p)
	c = Hash(p, g, k, t, m)
	z = (c*x + r)
	return (z,t,y,k)

def Verify(p, g, m, sign):
	z, t, y, k = sign
	c = Hash(p, g, k, t, m)
	lhs = (pow(y,c,p)*t)%p
	rhs = pow(g,z,p)
	#print(lhs,rhs)
	return True if lhs == rhs else False


def RabinMillerTest(n, s, d):
	y = randint(2,n-2)
	orig = y
	y = pow(y,d,n)
	if y == 1 or y == n-1:
		return True
	for i in range(s):
		y = (y*y)%n 
		if y == 1:
			return False 
		if y == n-1:
			return True

	return False

def isPrime(n):
	if n==0 or n == 1:
		return False 
	if n == 2 or n == 3:
		return True 
	if n%2 == 0:
		return False 

	d = n-1
	s = 0
	while(d%2==0):
		d //= 2
		s += 1

	n_witness = 100

	for i in range(n_witness):
		if not RabinMillerTest(n,s,d):
			return False

	return True


def generatePrime(n):
	iters = 0
	while True:
		iters += 1
		s = getrandbits(n-1)
		s = (s<<1) + 1
		if isPrime(s) and isPrime(2*s+1):
			# print(iters)
			return s



def findGenerator(q):
	p = 2*q+1
	while True:
		g = randint(2, p-1)

		if pow(g,q,p) == 1 or pow(g,2,p) == 1:
			continue

		return g



def encodeMessage(s):
	# return int(s.encode('hex'),16)
	return int.from_bytes(s.encode(), 'big')

def decodeMessage(n):
	return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode()