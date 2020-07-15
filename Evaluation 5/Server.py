import socket
import sys
from random import randint
import pickle
from Eval5 import ObliviousTransferData, ReedSolomon, ElGamalKey

BUFF_SIZE = 100000000
N_CONNECTIONS = 20
N_TOLERABLE_ERRS = 10
N_BLOCKS = N_CONNECTIONS - N_TOLERABLE_ERRS
CORRUPT_CHANNELS = [randint(0,N_CONNECTIONS-1) for i in range(N_TOLERABLE_ERRS)]

class SChannel:
	def __init__(self, port, PK, hashKey):
		self.port = port
		self.rs = ReedSolomon(PK, hashKey, N_BLOCKS, N_TOLERABLE_ERRS)
		try:
			self.servFd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except:
			# print("Failed at create socket")
			exit(1)

		self.servFd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.servFd.bind(("",port))
		except Exception as e:
			# print("Failed at Bind")
			# print(e)
			exit(1)

	def sendUtil(self, enc, addr):
		j = 0
		for c in enc:
			if j in CORRUPT_CHANNELS:
				print("\tCorrupting ",j)
				self.rs.Corrupt(c)
			
			m_bytes = pickle.dumps(c)
			print("\t Sending block ",j)
			j+=1
			self.servFd.sendto(m_bytes, addr)

	
	def send(self, message, addr):

		by = pickle.dumps(message)
		encArr = self.rs.Encode(by)

		ln = len(encArr)
		print("Generated |g| = {} groups of length n = {}".format(ln, len(encArr[0])))
		lEncode = self.rs.Encode(pickle.dumps(ln))
		print("Sending |g|")
		self.sendUtil(lEncode[0],addr)

		i = 0
		for enc in encArr:
			print("Sending group ",i)
			i+=1
			self.sendUtil(enc, addr)

	def recvUtil(self, i):

		recvby,addr = self.servFd.recvfrom(BUFF_SIZE)
		c = pickle.loads(recvby)
		print("\t Received block ",i)
		return c,addr

	def recvOnce(self):
		code = []
		addr = ""
		for i in range(N_CONNECTIONS):
			c,addr = self.recvUtil(i)

			code.append(c)

		parry = self.rs.Decode(code)

		return parry,addr

	def decodeParry(self, m):

		n = self.rs.P_arry2Dec(m)
		s = n.to_bytes((n.bit_length() + 7) // 8, 'big')
		m = pickle.loads(s)

		return m
		
	def recv(self):

		ln,addr = self.recvOnce()
		ln = self.decodeParry(ln)
		print("Recieved |g| = ",ln)

		m = []
		for i in range(ln):
			mi,addr = self.recvOnce()
			m.extend(mi)
			print("Recieved group ",i)

		m = self.decodeParry(m)
		return m,addr


with open('PK','rb') as of:
	PK = pickle.load(of)
with open('SK','rb') as of:
	SK = pickle.load(of)
with open('hashKey','rb') as of:
	hashKey = pickle.load(of)
with open('key','rb') as of:
	key = pickle.load(of)


c = SChannel(20001, PK, hashKey)
data = eval(input("Enter Data in List form "))
# data = [1,2,3,4,5]
print(data)
OTD = ObliviousTransferData(key, data)

while True:
	
	# print("RECEIVING start")
	msg,addr = c.recv()
	if msg != 'start':
		continue

	print("Generating Random Array r of size ",len(data))
	r = OTD.genRandom()
	print("Sending r to client")
	c.send(r,addr)
	print("Receiving v from client")
	v,addr = c.recv()
	print("Generating k using v")
	k = OTD.genK(v)
	print("Sending k to client")
	c.send(k,addr)

