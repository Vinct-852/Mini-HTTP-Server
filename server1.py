import socket
import threading
import os
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime

# the WebServer class initializes a socket that listens on the specified host and port.
class WebServer:
    def __init__(self, host, port):
        # host ip
        self.host = host
        # prot number
        self.port = port
        # create a socket object
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set socket options
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind to the port
        self.server_socket.bind((self.host, self.port))

# Content Type Identifier
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt": "text/html; charset=utf-8",
        ".html": "text/html; charset=utf-8"
    }

# start method accepts incoming connections and starts a new thread to handle each request.
    def start(self):
        self.server_socket.listen(5)
        print(f"Server is listening on {self.host}:{self.port}...")

        while True:
            # Wait for client connections
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection from {client_address}...")

            # Start a new thread to handle the request
            client_thread = threading.Thread(target=self.handle_request, args=(client_socket, client_address,))
            # threads.append(client_thread)
            client_thread.start()
  
# handle_request method reads the request data, parses the requested file path, 
# and returns the requested file or a 404 error if the file is not found.
    def handle_request(self, client_socket, client_address):
        
        # Get and heandle the client request
        request_data = client_socket.recv(1024).decode()
        headers, body = request_data.split("\r\n\r\n", 1)
        headers = headers.split("\r\n")
        request_line = headers.pop(0)
        headers = dict(header.split(": ", 1) for header in headers)
        
        # Get the If-Modified-Since header from the request
        if_modified_since = headers.get("If-Modified-Since")
        
        # Get the Connection field from the request
        keep_alive = False
        connection = headers.get('Connection')
        # Check if the connection is keep-alive 
        if(connection == 'keep-alive'):
            keep_alive = True
            alive = headers.get('Keep-Alive')
            alive = alive.split(", ")
            alive = dict(inform.split("=", 1) for inform in alive)
        
        # Get the time
        current_time = formatdate(timeval=None, localtime=False, usegmt=True)

        # identify the http request and handling invalid request
        try:
            request_type = request_data.split()[0]
        except IndexError:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid Request".encode()
            client_socket.sendall(response)
            client_socket.close()
            return
        
        # Parse the request data to get the requested file path
        try:
            path = request_data.split()[1]
        except IndexError:
            path = '/index.html'   
        if(path == '/'):
            path = '/index.html'
        
        # determine Content-Type
        extension = path.split('.')[-1]
        content_type = self.content_types.get('.' + extension)   
              
        # Record statistics of the client requests
        with open('log.txt', 'a') as f:
            f.write(f'ClientIP: {client_address} | ')
            f.write(f'Access Time: {current_time} | ')
            f.write(f'Requested File Name: {path} | ')
            f.write(f'Response Type: {content_type}') 
            f.write('\n')
        
        # Get the last modification time of the file as a timestamp
        # Check if the requested file exit
        try:
            timestamp = os.path.getmtime('.'+path)
        except FileNotFoundError:
            response = "HTTP/1.1 404 Not Found\r\n\r\n File Not Found".encode()
            client_socket.sendall(response)
            client_socket.close()
            return
        last_modified_datetime = datetime.fromtimestamp(timestamp)
        http_last_modified_datetime = last_modified_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Handle Last-Modified and If-Modified-Since header fields
        if if_modified_since:
            last_modified_datetime = last_modified_datetime.replace(tzinfo=timezone.utc)
            if_modified_since_datetime = parsedate_to_datetime(if_modified_since)
            
            # Check if the file has not been modified or not
            if last_modified_datetime <= if_modified_since_datetime:
                response = f"HTTP/1.1 304 Not Modified\r\nDate: {current_time}\r\n\r\n".encode()
                client_socket.sendall(response)
                client_socket.close()
                return
        
        # GET command for both text files and image files
        if(request_type == "GET"):
            # Get the time
            current_time = formatdate(timeval=None, localtime=False, usegmt=True)  
                
            # Return the requested file with header
            with open("." + path, "rb") as file:
                response_data = file.read()
                response_headers = "HTTP/1.1 200 OK\r\n"
                response_headers += f"Date: {current_time}\r\n"
                response_headers += f"Last-Modified: {http_last_modified_datetime}\r\n"
                response_headers += f"Content-Type: {content_type}\r\n"
                response_headers += f"Content-Length: {len(response_data)}\r\n"
                response_headers += "\r\n"
                response = response_headers.encode() + response_data                  
        
        # HEAD command     
        elif(request_type == 'HEAD'):
            # Get the time
            current_time = formatdate(timeval=None, localtime=False, usegmt=True)
            
            # Return the header only
            with open("." + path, "rb") as file:
                response_data = file.read()
                response_headers = "HTTP/1.1 200 OK\r\n"
                response_headers += f"Date: {current_time}\r\n"
                response_headers += f"Last-Modified: {http_last_modified_datetime}\r\n"
                response_headers += f"Content-Type: {content_type}\r\n"
                response_headers += f"Content-Length: {len(response_data)}\r\n"
                response_headers += "\r\n"
                response = response_headers.encode()
        else:
            response = "HTTP/1.1 400 Bad Request\r\n\r\n Invalid Request".encode()
        
        # Send HTTP response
        client_socket.sendall(response)
        
        client_socket.close()

if __name__ == "__main__":
    server = WebServer("localhost", 8080)
    server.start()
