Multi-threaded Web server

You can start the server by creating a server object
For example: we you want to instantiated with the hostname "localhost" and port number 8080

    if __name__ == "__main__":
        server = WebServer("localhost", 8080)
        server.start()

*IMPORTANT*
1.This server can only supporting GET and HEAD requests *(other requests would be consider invalid)
2.and have four types of response statuses ONLY (including 200 OK, 400 Bad Request, 404 File Not Found, 304 Not Modified).
3.This server support handling Last-Modified and If-Modified-Since header fields
4.and handling Connection: Keep-Alive header field 

*TESTING*
You can do testing by implement your own client program or use the TCPClient.py from the folder directly.

You can change the "command"(which is http request) in line 21 to send a request to the server and receive the respond. For example, command = "GET /index.html HTTP/1.1\r\nConnection: keep-alive\r\n\r\n"