import sys
import socket
# get urls_file name from command line
if len(sys.argv) != 2:
    print('Usage: monitor urls_file')
    sys.exit()
    
# text file to get list of urls
urls_file = sys.argv[1]
# server, port, and path should be parsed from url
host = 'inet.cs.fiu.edu'
port = 80 # use port 80 for http and port 443 for https
path = '/'
sock = None
# create client socket, connect to server

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))
except Exception as e:
    print(f'Network Error:\n {e}')
if sock:
    # send http request
    request = f'GET {path} HTTP/1.0\r\n'
    request += f'Host: {host}\r\n'
    request += '\r\n'
    sock.send(bytes(request, 'utf-8'))
    # receive http response
    response = b''
    while True:
        data = sock.recv(4096)
        response += data
        if not data:
            break
    print(response.decode('utf-8'))
    sock.close()
