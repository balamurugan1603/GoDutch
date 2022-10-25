import socket  
import pandas as pd
import ast
import sys

sys.path.append('..')

from ml.LinearRegression import DistributedLinearRegression

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

def create_client(server_port, client_port):
    s = socket.socket()          
    s.bind(('', client_port))
    s.connect(('127.0.0.1', server_port))

    data = recvall(s).decode()    # recv(10240)
    data = pd.DataFrame.from_dict(ast.literal_eval(data)["data"], orient = "columns").values

    lr = DistributedLinearRegression()

    lr.fit(data[:, :-1], data[:, -1], num_epochs= 30)
    theta = lr.get_weights()
    print(lr.cost_list)
    print(theta)
    s.send(str(theta).encode())
    print(f"Job successful. Closing connection from {client_port}")
    s.close()

