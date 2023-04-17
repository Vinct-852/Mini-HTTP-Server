# import the socket library
import socket
from email.utils import formatdate

# create a socket object
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# define the server's name and port on which you want to connect
serverName = 'localhost'
serverPort = 8080

# connect to the server
clientIP = '127.0.0.1' # because this is an example, we use the default localhost
clientPort = 34115
clientSocket.bind(('', clientPort))
clientSocket.connect((serverName, serverPort))

isImg = False
if_modified_since = 'Sun, 14 Mar 2024 17:16:25 GMT'
# command = "GET /index.html HTTP/1.1\r\n\r\n"
# command = "GET /capybara1.jpeg HTTP/1.1\r\n\r\n"
# isImg = True
# command = "HEAD /index.html HTTP/1.1\r\n\r\n"
# command = "HEAD /capybara1.jpeg HTTP/1.1\r\n\r\n"
# command = "GET /capy.jpeg HTTP/1.1\r\n\r\n"
# command = "HEAD /capy.jg HTTP/1.1\r\n\r\n"
# command = "HEA /index.html HTTP/1.1\r\n\r\n"
command = f"GET / HTTP/1.1\r\nIf-Modified-Since: {if_modified_since}\r\n\r\n"

clientSocket.send(str(command).encode())

with open('record.txt', 'a') as f:
    f.write(f'*HTTP Request sent by {clientIP}:*\n')
    f.write(command)
    f.write(f'*HTTP Respond from {serverName}:*\n')

# Receive the response from the server
response = b''
while True:
    data = clientSocket.recv(1024)
    if not data:
        break
    response += data

# Parse the response to extract the file data
header, file_data = response.split(b'\r\n\r\n', 1)

# Save the file data to a local file
with open('record.txt', 'ab') as f:
    f.write(header)
    if not isImg:
        f.write(file_data)
    

with open('record.txt', 'a') as f:
    f.write('\n\n')

if isImg:
    with open('img.jpeg', 'wb') as f:
        f.write(file_data)

# Close the socket
clientSocket.close()
