import socket
import pandas as pd
import ast
import sys
import argparse
import requests
from requests.auth import HTTPBasicAuth

sys.path.append('..')

from ml.LinearRegression import DistributedLinearRegression

parser = argparse.ArgumentParser()

parser.add_argument("--email", type=str)
parser.add_argument("--password", type=str)
parser.add_argument("--device_name", type=str)
parser.add_argument("--exp_id", type=int)

args = parser.parse_args()
dateformat = r"%d-%m-%Y %H:%M:%S"

body = {
    "id": args.exp_id,
    "device_name": args.device_name,
    "device_type": 0
}

url = "http://172.18.132.255:5000/experiments/commit"

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

def create_node(server_port, client_port):
    s = socket.socket()          
    s.bind(('', client_port))
    s.connect(('127.0.0.1', server_port))

    data = recvall(s).decode()    # recv(10240)
    data = pd.DataFrame.from_dict(ast.literal_eval(data)["data"], orient = "columns").values

    lr = DistributedLinearRegression()

    lr.fit(data[:, :-1], data[:, -1], num_epochs= 30)
    theta = lr.get_weights()
    body["metrics"] = lr.cost_list
    response = requests.post(
        url,
        json = body,
        auth = HTTPBasicAuth(
            args.email, args.password
        )
    )
    print(lr.cost_list)
    print(theta)
    s.send(str(theta).encode())
    print(f"Job successful. Closing connection from {client_port}")
    s.close()

