# Uncomment this to pass the first stage
import socket
from threading import Thread
import os
import argparse
#Constants
HOST = "localhost"
PORT = 4221
# UDF
def user_agent_handler(user_agent:str)->str:
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}".encode()

def echo_handler(path:str)->str:
    body = path.lstrip("/echo/")
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: { len(body)}\r\n\r\n{body}".encode())

def get_files_handler(directory:str,path:str) -> str:
    file_name = path.split("/files/")[-1]
    file_path = os.path.join(directory, file_name)
    # Check if the file exists at the filepath
    if os.path.isfile(file_path):
        with open(file_path,"r") as file_buffer:
            file_content = file_buffer.read()

            content_type = "Content-Type: application/octet-stream"

            content_len = f"Content-Length: {len(file_content)}"

            status_line = "HTTP/1.1 200 OK"

            http_res = f"{status_line}\r\n{content_type}\r\n{content_len}\r\n\r\n{file_content}\r\n\r\n"
            return http_res
    else:
        not_found = "HTTP/1.1 404 NOT FOUND\r\n\r\n"
        return not_found

def post_files_handler(directory:str,path:str,content:str):
    file_name = path.split("/files/")[-1]
    file_path = os.path.join(directory, file_name)
    with open(f"{file_path}","w") as file_buffer:
        file_buffer.write(content)
    return f"HTTP/1.1 201\r\n\r\n"

def router(stream:socket,rec_add,directory):
    while True:
        req_data = stream.recv(4096).decode()
        if not req_data:
            return
        req_lines:list[str] = req_data.strip().split("\r\n")
        method,path,version = req_lines[0].split(" ")
        if path == "/":
            http_res = "HTTP/1.1 200 OK\r\n\r\n"
            stream.send(http_res.encode())
        elif path.startswith("/user-agent"):
            #Obtain the user agent content
            user_agent = req_lines[2].split(": ")[1]
            stream.sendall(user_agent_handler(user_agent))

        elif path.startswith("/echo/"):
            stream.sendall(echo_handler(path))

        elif path.startswith("/files/"):
            if method == "GET":
                response_file = get_files_handler(directory,path).encode()
                stream.send(response_file)
            if method == "POST":
                content = req_lines[-1].strip()
                stream.send(post_files_handler(directory,path,content).encode())
        else:
            bad_request = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
            stream.send(bad_request)
        stream.close()
# Main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="File serving directory")
    args = parser.parse_args()
    server_socket = socket.create_server((HOST, PORT), reuse_port=True)
    try:
        while True:
                stream, _addr = server_socket.accept()
                thread = Thread(target=router, args=(stream, _addr, args.directory))
                thread.start()
    except KeyboardInterrupt:
        print("Server shutt down!")

if __name__ == "__main__":
    main()
