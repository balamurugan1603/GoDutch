import socket
from _thread import *
import pandas as pd
import numpy as np
import argparse
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from ml.LinearRegression import DistributedLinearRegression

parser = argparse.ArgumentParser()

parser.add_argument("--email", type=str)
parser.add_argument("--password", type=str)
parser.add_argument("--exp_name", type=str)
parser.add_argument("--exp_id", type=int)
parser.add_argument("--desc", type=str)

args = parser.parse_args()
dateformat = r"%d-%m-%Y %H:%M:%S"

body = {
    "device_type": 1,
    "id": args.exp_id,
    "name": args.exp_name,
    "description": args.desc,
    "active": 1,
    "start": datetime.now().strftime(dateformat)
}

url = "http://0.0.0.0:5000/experiments/commit"
response = requests.post(
    url,
    json = body,
    auth = HTTPBasicAuth(
        args.email, args.password
    )
)

if response.content != b'1':
    print("Unsuccessful !")
    print("Run the script again !")
    exit()


def recvall(sock):
    BUFF_SIZE = 4096 # 4 KiB
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 2004
connectport = [12345, 12346]  #, 12346, 12347
nworkers = len(connectport)
ThreadCount = 0

try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Socket is listening..')
ServerSideSocket.listen(5)

# data = pd.read_csv("master/cleaned.csv").to_json(orient = 'table', index = False)
df = pd.read_csv("cleaned_normalised.csv")
df_shuffled = df.sample(frac=1)
df_splits = np.array_split(df_shuffled, nworkers)
df_splits = [
    df_split.to_json(
        orient = 'table',
         index = False
    ) for df_split in df_splits]

thetas = []
completed = [nworkers]

def multi_threaded_client(connection, data, thetas, completed):
    connection.sendall(data.encode())
    print("Distributed")
    data = recvall(connection).decode()
    print("received")
    thetas.append(data)
    connection.close()
    completed[0] -= 1

i = 1
while(i <= nworkers):
    conn, addr = ServerSideSocket.accept()
    print(addr)
    if addr[1] not in connectport:
        conn.close()
        i -= 1
    else:
        # do what ever you want here
        print('Connected to: ' + addr[0] + ':' + str(addr[1]))
        start_new_thread(multi_threaded_client, (conn, df_splits[i-1], thetas, completed))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))
    i += 1

while(completed[0] != 0):
    pass

lr = DistributedLinearRegression()

def literal_eval(lst):
    lst = lst[1:len(lst)-1]    # Removes '[', ']'
    lst = list(map(float, lst.split()))
    return lst

thetas = np.array(list(map(literal_eval, thetas)))
print(thetas)

lr.from_weights(thetas)
theta = lr.get_weights()
print(theta)

print("Closing server")
ServerSideSocket.close()

body["active"] = 0
body["end"] = datetime.now().strftime(dateformat)
body["weights"] = list(theta)

response = requests.post(
    url,
    json = body,
    auth = HTTPBasicAuth(
        args.email, args.password
    )
)

print("Execution successful !")