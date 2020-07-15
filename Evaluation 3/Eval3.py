from random import randint,getrandbits
from math import log,ceil


class GroupGen:

	def RabinMillerTest(self, n, s, d):
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

	def isPrime(self, n):
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
			if not self.RabinMillerTest(n,s,d):
				return False

		return True

	def generatePrime(self, n):
		iters = 0
		while True:
			iters += 1
			s = getrandbits(n-1)
			s = (s<<1) + 1
			if self.isPrime(s) and self.isPrime(2*s+1):
				# print(iters)
				return s

	def findGenerator(self, q):
		p = 2*q+1
		while True:
			g = randint(2, p-1)

			if pow(g,q,p) == 1 or pow(g,2,p) == 1:
				continue

			return g


class HashClass:

	def __init__(self, prime_length = 128):
		gen = GroupGen()
		self.q = gen.generatePrime(prime_length)
		self.p = 2*self.q+1
		self.g = gen.findGenerator(self.q)
		self.k = randint(1,self.p-1)

	def h(self, x, y):
		#print("woah",x,y)
		y = int(y,2)

		assert(x<self.p and y<self.p)
		return (pow(self.g,x,self.p)*pow(self.g,y,self.p))%self.p


	def MerkleDamgard(self, x, l):
		l = 2*(l-1) - l
		L = len(x)
		B = int(L/l)
		rem = L%l 
		# pad with zero to make it a multiple of l
		x += "0"*((B+1)*l - rem)
		B += 1

		# binL = bin(L)[2:]
		# rem = l - len(binL)

		z = self.p-1
		for i in range(1,B+1):
			xi = x[(i-1)*l:i*l]
			z = self.h(z, xi)
			#print("result ",z)

		return z


	def Hash(self, t, m):
		ms = bin(t)[2:] + bin(m)[2:]
		l = int(log(self.p,2))+1
		z = self.MerkleDamgard(ms, l)
		
		#print("Final Hash ",int(z))
		return int(z)



class Signature:

	def __init__(self, prime_length=128):
		gen = GroupGen()
		self.q = gen.generatePrime(prime_length)
		self.p = 2*self.q+1
		self.g = gen.findGenerator(self.q)
		self.hashObj = HashClass()


	def Gen(self):
		x = randint(1,self.p-1)
		y = pow(self.g, x, self.p)
		return x,y

	def Sign(self, m):
		x,y = self.Gen()
		#print("x y k",x,y,k)
		r = randint(1,self.p-1)
		t = pow(self.g,r,self.p)
		c = self.hashObj.Hash(t, m)
		z = (c*x + r)
		return (z,t,y)

	def Verify(self, m, sign):
		z, t, y = sign
		c = self.hashObj.Hash(t, m)
		lhs = (pow(y,c,self.p)*t)%self.p
		rhs = pow(self.g,z,self.p)
		#print(lhs,rhs)
		return True if lhs == rhs else False


# Global Dictionary to simulate pointers
memory = {}

class Pointer:

	def __init__(self, val):
		memory[id(self)] = val

	def star(self):
		return memory[id(self)]

	def addr(self):
		return id(self)

class HashPointer(Pointer):

	def __init__(self, val):
		Pointer.__init__(self, val)
		self.hashObj = HashClass()
		a,b = val.get()
		self.hash = self.hashObj.Hash(a,b)

	def checkHash(self):
		a,b = self.star().get()
		if self.hashObj.Hash(a,b) == self.hash:
			return True
		return False

class HashSignPointer(HashPointer):

	def __init__(self, val, signObj):
		HashPointer.__init__(self, val)
		a,b = val.get()
		self.sign = signObj.Sign(int(str(a)+str(b)))

	def checkSign(self, signObj):
		a,b = self.star().get()
		return signObj.Verify(int(str(a)+str(b)), self.sign)


class Node:

	def __init__(self, val, nex):
		self.val = val
		self.nex = nex

	def get(self):
		n = int.from_bytes(self.val.encode(), 'big')
		idn = id(self.nex)
		return (n,idn)


class PointerStack:

	def __init__(self):
		self.top = Pointer(Node("",None))
		self.size = 0

	def push(self, val):
		tmp = self.top.star().nex
		self.top.star().nex = Pointer(Node(val, tmp))
		self.size += 1

	def front(self):
		if self.size == 0:
			return None
		tmp = self.top.star().nex
		return tmp.star().val

	def pop(self):
		if self.size == 0:
			return 

		tmp = self.top.star().nex
		self.top.star().nex = tmp.star().nex
		self.size -= 1


class HashPointerStack:

	def __init__(self):
		self.top = HashPointer(Node("",None))
		self.size = 0

	def push(self, val):
		tmp = self.top.star().nex
		self.top.star().nex = HashPointer(Node(val, tmp))
		self.size += 1

	def front(self):
		if self.size == 0:
			return None
		tmp = self.top.star().nex
		return tmp.star().val

	def pop(self):
		if self.size == 0:
			return 

		tmp = self.top.star().nex
		self.top.star().nex = tmp.star().nex
		self.size -= 1


class HashSignPointerStack:

	def __init__(self):
		self.top = HashSignPointer(Node("",None), Signature())
		self.size = 0

	def push(self, val, signObj):
		tmp = self.top.star().nex
		self.top.star().nex = HashSignPointer(Node(val, tmp), signObj)
		self.size += 1

	def front(self):
		if self.size == 0:
			return None
		tmp = self.top.star().nex
		return tmp.star().val

	def pop(self):
		if self.size == 0:
			return 

		tmp = self.top.star().nex
		self.top.star().nex = tmp.star().nex
		self.size -= 1


