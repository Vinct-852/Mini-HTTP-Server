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
        # client list
        self.clients_IPs = {}

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
            # client_thread = threading.Thread(target=self.handle_request_V1, args=(client_socket, client_address,))
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address,))
            self.clients_IPs[client_address] = client_thread
            client_thread.start()
                
    def handle_client(self, client_socket, client_address):
        # Set a timeout of 60 seconds and max requests of 3 on the connection
        timeOut = 5
        client_socket.settimeout(timeOut)
        keepAlive = False
        max_request = 100
        request_handled = 0
        
        # handle the max request part for the Keep-Alive    
        while (max_request > request_handled):     
            try:
                # Get and heandle the client request
                try:
                    request_data = client_socket.recv(1024).decode()
                except ConnectionAbortedError:
                    break             
                       
                if request_data:
                    # Request handling
                    request_handled+=1  
                    client_thread = threading.Thread(target=self.handle_request_V2, args=(client_socket, client_address, request_data, keepAlive, timeOut, max_request,))
                    client_thread.start()
                    client_thread.join()
                    # noExcept = self.handle_request_V2(client_socket, client_address, request_data, keepAlive, timeOut, max_request)
                
                    if noExcept:
                        headers, body = request_data.split("\r\n\r\n", 1)
                        headers = headers.split("\r\n")
                        request_line = headers.pop(0)
                        headers = dict(header.split(": ", 1) for header in headers)

                        # Get the Connection field from the request
                        connection = headers.get('Connection')
                                                        
                        # Check if the connection is keep-alive 
                        if(connection == 'keep-alive'):
                            keepAlive = True

                    if not keepAlive:
                        client_socket.close()
                        print(f"{client_address} disconnected")
                        del self.clients_IPs[client_address]
                        break
                else:
                    # request_data is 0
                    response = "HTTP/1.1 400 Bad Request\r\n\r\n Invalid Request".encode()
                    client_socket.sendall(response)
                    
            except socket.timeout:
                    print(f'connection {client_address} timed out')
                    client_socket.close()
                    print(f"{client_address} disconnected")
                    del self.clients_IPs[client_address]
                    return
        
        print(f'{max_request} {request_handled}')
        if(max_request < request_handled):
            print(f'connection {client_address} reach limit requests')
        else:
            print(f'connection {client_address} closed connection')        
        client_socket.close()
        print(f"{client_address} disconnected")
        del self.clients_IPs[client_address]
                
    # KEEP-ALIVE HANDLING        
    # handle_request method reads the request data, parses the requested file path, 
    # and returns the requested file or a 404 error if the file is not found. 
    def handle_request_V2(self, client_socket, client_address, request_data, keepAlive, timeOut, max_request):
        terminate = False
        
        # Split the http request headers to request and other headers
        try:
            headers, body = request_data.split("\r\n\r\n", 1)
            headers = headers.split("\r\n")
            request_line = headers.pop(0)
            headers = dict(header.split(": ", 1) for header in headers)
        except:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid Request".encode()
            client_socket.sendall(response)
            terminate = True
        
        # Get the time
        current_time = formatdate(timeval=None, localtime=False, usegmt=True)
        
        # identify the http request and handling invalid request
        try:
            request_type = request_data.split()[0]
        except IndexError:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid Request".encode()
            client_socket.sendall(response)
            terminate = True
        
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
        
        if terminate: return False
        
        # Get the Connection field from the request
        connection = headers.get('Connection')
                                        
        # Check if the connection is keep-alive 
        if(connection == 'keep-alive'):
            keepAlive = True
                        
        # Get the If-Modified-Since header from the request
        if_modified_since = headers.get("If-Modified-Since")
        
        # Get the last modification time of the file as a timestamp
        # Check if the requested file exit
        try:
            timestamp = os.path.getmtime('.'+path)
        except FileNotFoundError:
            response = "HTTP/1.1 404 Not Found\r\n\r\n File Not Found".encode()
            client_socket.sendall(response)
            return True
        
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
                return True
        
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
                if keepAlive: response_headers += f"Connection: Keep-Alive\r\n"
                if keepAlive: response_headers += f"Keep-Alive: timeout={timeOut}, max={max_request}\r\n"
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
                if keepAlive: response_headers += f"Connection: Keep-Alive\r\n"
                if keepAlive: response_headers += f"Keep-Alive: timeout={timeOut}, max={max_request}\r\n"
                response_headers += "\r\n"
                response = response_headers.encode()
        else:
            response = "HTTP/1.1 400 Bad Request\r\n\r\n Invalid Request".encode()
        
        # Send HTTP response
        client_socket.sendall(response)
        return True
  
    # handle_request method reads the request data, parses the requested file path, 
    # and returns the requested file or a 404 error if the file is not found.
    def handle_request_V1(self, client_socket, client_address):
        
        # Get and heandle the client request
        request_data = client_socket.recv(1024).decode()
        headers, body = request_data.split("\r\n\r\n", 1)
        headers = headers.split("\r\n")
        request_line = headers.pop(0)
        headers = dict(header.split(": ", 1) for header in headers)
        
        # Get the If-Modified-Since header from the request
        if_modified_since = headers.get("If-Modified-Since")
        
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
