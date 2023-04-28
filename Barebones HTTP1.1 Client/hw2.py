'''
Ajitesh Bansal
'''

import logging
import socket
import sys

def retrieve_url(url):
    
    main_path = parse_url(url)

    if main_path is None:
        return None

    major_response = main_communication(main_path)
    return major_response

def parse_url(url):
    
    parse_list_all = []
    url_length = len(url)

    if url.find("http://", 0, 7) != -1:
        parse_list_all = (url[7:url_length].split("/", 1))
        if len(parse_list_all) < 2 or parse_list_all[1] == "":
            path = "/"
        else:
            path = "/" + parse_list_all[1]
        split_port = parse_list_all[0].split(":", 1)
        host = split_port[0]
        if len(split_port) == 2:
            port = int(split_port[1])
        else:
            port = 80
        website_services = [host, path, port]
        return website_services
    elif url.find("https://", 0, 8) != -1:
        parse_list_all = (url[8:url_length].split("/", 1))
        if len(parse_list_all) < 2 or parse_list_all[1] == "":
            path = "/"
        else:
            path = "/" + parse_list_all[1]
        split_port = parse_list_all[0].split(":", 1)
        host = split_port[0]
        if len(split_port) == 2:
            port = int(split_port[1])
        else:
            port = 80
        website_services = [host, path, port]
        return website_services

    else:
        return None

    


def create_request(main_path):
    
    request = ("GET " + main_path[1] +
               " HTTP/1.1\r\nHost:" + main_path[0] +
               "\r\nConnection: close\r\n\r\n")
    return request



def main_communication(main_path):
    
    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        main_socket.connect((main_path[0], int(main_path[2])))
        request = create_request(main_path)
        main_socket.send(request.encode())
    except socket.error:
        return None

    data_packets = []
    while True:
        data = None
        try:
            data = main_socketrecv(4096)

            if data:
                data_packets.append(data)
                data = None
                continue
            else:
                break
        except socket.error:
            return None
    send_back = b"".join(data_packets)
    data = send_back
    if data.find(b"200 OK", 0, len(data)) != -1:
        new_data = data.split(b"\r\n\r\n", 1)
        return new_data[1]

if __name__ == "__main__":
        
    sys.stdout.buffer.write(retrieve_url(sys.argv[1])) # pylint: disable=no-member 
