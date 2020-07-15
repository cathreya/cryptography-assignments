from random import randint,getrandbits
from math import log,ceil

class Signature:

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

	def __init__(self, prime_length=256):
		self.q = self.generatePrime(prime_length)
		self.p = 2*self.q+1
		self.g = self.findGenerator(self.q)
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


	def Gen(self):
		x = randint(1,self.p-1)
		y = pow(self.g, x, self.p)
		return x,y

	def Sign(self, m):
		x,y = self.Gen()
		#print("x y k",x,y,k)
		r = randint(1,self.p-1)
		t = pow(self.g,r,self.p)
		c = self.Hash(t, m)
		z = (c*x + r)
		return (z,t,y)

	def Verify(self, m, sign):
		z, t, y = sign
		c = self.Hash(t, m)
		lhs = (pow(y,c,self.p)*t)%self.p
		rhs = pow(self.g,z,self.p)
		#print(lhs,rhs)
		return True if lhs == rhs else False


def encodeMessage(s):
	# return int(s.encode('hex'),16)
	return int.from_bytes(s.encode(), 'big')

def decodeMessage(n):
	return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode()


class ReedSolomon:

	def __init__(self, p, k, e):
		self.p = p
		self.k = k
		self.e = e
		self.a = [i for i in range(1,k+e+1)]
		self.sign = Signature(128)

	def C(self, m):
		c = []
		for i in range(len(self.a)):
			a_i = 1
			res = 0
			for j in range(len(m)):
				res += (m[j]*a_i)%self.p
				res %= self.p
				a_i *= self.a[i];
				a_i %= self.p

			c.append(res)

		return c

	def Dec2P_arry(self, m):
		ar = []
		while m>0:
			ar.append(m%self.p)
			m//=self.p
		return ar

	def P_arry2Dec(self, l):
		dec = 0
		for i in range(len(l)):
			dec += l[i]*pow(self.p,i)
		return dec

	def Encode(self, message):
		m = int.from_bytes(message.encode(), 'big')
		# print("Encoded ",m)
		m = self.Dec2P_arry(m)
		# print("Encoded ",m)
		if(len(m) > self.k):
			print("Message Exceeds k blocks")
			return None

		c = self.C(m)
		print(len(c))
		code = []
		for i in c:
			code.append([i,self.sign.Sign(i)])

		return code

	def Corrupt(self, code):

		for i in range(self.e):
			ind = randint(0,len(code)-1)
			print("Corrupting index {}".format(ind))
			noise = randint(0,self.p-1)
			code[ind][0] ^= noise

		return code


	def inv(self, n):
		return pow(n,self.p-2,self.p)

	def GaussElim(self, A, b):
		mat = []
		for i in range(len(A)):
			row = []
			for j in range(len(A)):
				row.append(pow(A[i],j,self.p))
			row.append(b[i])
			mat.append(row)
			# mat.append(A[i])
			# mat[i].append(b[i])


		row = [-1 for i in range(len(A))]
		R = len(mat)
		C = R
		r = 0
		mod = self.p
		for c in range(C):
			k = r
			while k<R and mat[k][c] == 0:
				k+=1
			if k==R:
				continue

			mat[k],mat[r] = mat[r],mat[k]

			div = self.inv(mat[r][c])
			for i in range(R):
				if i != r:
					w = mat[i][c]*(mod-div)%mod
					for j in range(C+1):
						mat[i][j] = (mat[i][j] + mat[r][j] * w)%mod

			row[c] = r
			r += 1

		ans = [0 for i in range(C)]
		for i in range(C):
			r = row[i]
			ans[i] = (mat[r][C] * self.inv(mat[r][i]))%mod

		return ans


	def Decode(self, code):
		inds = []
		for i in range(len(code)):
			if self.sign.Verify(code[i][0],code[i][1]):
				print("Index {} is not corrupted".format(i))
				inds.append(i)

			if len(inds) == self.k:
				break

		A = [self.a[i] for i in inds]
		b = [code[i][0] for i in inds]

		# print(self.k, inds)
		# print(A,b)

		msg = self.GaussElim(A,b)

		# print("Decoded ",msg)
		n = self.P_arry2Dec(msg)
		# print("Decoded ", n)
		s = n.to_bytes((n.bit_length() + 7) // 8, 'big').decode()

		return s



