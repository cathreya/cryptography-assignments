import socket
import sys
import pickle
from random import randint
from Eval5 import ObliviousTransferIndex, ReedSolomon, ElGamalKey

BUFF_SIZE = 100000000
N_CONNECTIONS = 20
N_TOLERABLE_ERRS = 10
N_BLOCKS = N_CONNECTIONS - N_TOLERABLE_ERRS
SERV_ADDR = ("",20001)
CORRUPT_CHANNELS = [randint(0,N_CONNECTIONS-1) for i in range(N_TOLERABLE_ERRS)]

class CChannel:
	def __init__(self, port, PK, hashKey):
		self.port = port
		self.rs = ReedSolomon(PK, hashKey, N_BLOCKS, N_TOLERABLE_ERRS)
		try:
			self.cliFd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except:
			# print("Failed at create socket")
			exit(1)

	
	def sendUtil(self, enc):
		
		j = 0
		for c in enc:
			if j in CORRUPT_CHANNELS:
				print("\tCorrupting ",j)
				self.rs.Corrupt(c)
			m_bytes = pickle.dumps(c)
			print("\t Sending block ",j)
			j+=1
			self.cliFd.sendto(m_bytes, SERV_ADDR)

	def send(self, message):

		by = pickle.dumps(message)
		encArr = self.rs.Encode(by)

		ln = len(encArr)
		print("Generated |g| = {} groups of length n = {}".format(ln, len(encArr[0])))
		lEncode = self.rs.Encode(pickle.dumps(ln))
		print("Sending |g|")
		self.sendUtil(lEncode[0])

		i = 0
		for enc in encArr:
			print("Sending group ",i)
			i+=1
			self.sendUtil(enc)

	def recvUtil(self, i):

		recvby,_ = self.cliFd.recvfrom(BUFF_SIZE)
		c = pickle.loads(recvby)
		print("\t Received block ",i)
		return c

	def recvOnce(self):
		code = []
		for i in range(N_CONNECTIONS):
			c = self.recvUtil(i)
			code.append(c)
		
		parry = self.rs.Decode(code)

		return parry

	def decodeParry(self, m):

		n = self.rs.P_arry2Dec(m)
		s = n.to_bytes((n.bit_length() + 7) // 8, 'big')
		m = pickle.loads(s)

		return m
		

	def recv(self):

		ln = self.recvOnce()
		ln = self.decodeParry(ln)
		print("Recieved |g| = ",ln)

		m = []
		for i in range(ln):
			mi = self.recvOnce()
			m.extend(mi)
			print("Recieved group ",i)

		m = self.decodeParry(m)
		return m





with open('PK','rb') as of:
	PK = pickle.load(of)
with open('hashKey','rb') as of:
	hashKey = pickle.load(of)

c = CChannel(20002, PK, hashKey)
ind = int(input("Enter index to request "))
# ind =  1
OTI = ObliviousTransferIndex(ind)

c.send("start")	
print("Receiving random array r from server")
r = c.recv()
print("Computing v")
v = OTI.sendV(r)
print("Sending v to server")
c.send(v)
print("Receiving k from server")
k = c.recv()
print("Recovering m_i from k")
m = OTI.getDatai(k)
print("Received data[i] = {}".format(m))
