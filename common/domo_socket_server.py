import gc
import socket

import domo_utils as d_u
import web_upload as w_u
import save_config as s_c

global cl

def start_socket_server(ipaddr, port):
    """
    Starts a socket server to handle HTTP requests for file uploads.

    Args:
        ipaddr (str): The IP address to bind the server to (e.g., '0.0.0.0').
        port (int): The port to listen on (e.g., 80).
    """
    d_u.print_and_store_log("Starting the Socket server")
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    soc.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    addr = socket.getaddrinfo(ipaddr, port)[0][-1]
    soc.bind(addr)
    soc.listen(5)
    d_u.print_and_store_log(f"SERVER: Listening on http://{ipaddr}:{port}")

    while True:
        cl = None
        try:
            gc.collect()
            cl, addr = soc.accept()
            d_u.print_and_store_log(f"SERVER: Client connected from {addr}")
            request = cl.recv(4096)
            if not request:
                cl.close()
                continue
            first_line = request.split(b'\r\n')[0]
            response = ""
            try:
                method, path, _ = first_line.decode('utf-8').split()
                d_u.print_and_store_log(f"SERVER: Received {method} request for {path}")
                if method == 'POST' and path.startswith('/upload/'):
                    response = w_u.handle_upload_simple(cl, soc, request, ipaddr)
                if method == 'POST' and path.startswith('/save_config'):
                    response = s_c.save_configuration(request)
                elif method == 'GET' and path == '/':
                    response = w_u.serve_file_upload_page(ipaddr, port)
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

            except Exception as err:
                d_u.print_and_store_log(f"SERVER: Error parsing request: {err}")
                response = "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"

            if response:
                if isinstance(response, tuple): # Handling responses like (content, status, headers)
                    content, status, headers = response
                    http_response = f"HTTP/1.1 {status}\r\n"
                    for k, v in headers.items():
                        http_response += f"{k}: {v}\r\n"
                    http_response += f"\r\n{content}"
                    cl.sendall(http_response.encode('utf-8'))
                else:
                    cl.sendall(response.encode('utf-8'))

            cl.close()

        except OSError as err:
            d_u.print_and_store_log(f"SERVER: Connection Error: {err}")
            if cl:
                cl.close()
        except Exception as err:
            d_u.print_and_store_log(f"SERVER: A critical error occurred: {err}")
            if cl:
                cl.close()
