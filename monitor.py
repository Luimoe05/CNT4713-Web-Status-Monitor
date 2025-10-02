import sys
import socket
import ssl
import re

TIMEOUT = 5

# ------[Parsing Url]--------
def parse_url(url):
    #We have 4 necessary things needed when we parse the url
    #PROTOCOL, PATH, HOST, PORT
    #Example http://example.com/hello
    #Host: example.com | Protocol: http | Path: /hello | Port: 80

    protocol = None 
    path = '/'
    host = None

    if(url.startswith('https://')):
        #set the port to 443 IF it starts with https://
        port = 443
        protocol = 'https'
        url = url[8:] #url[8:] makes it so we can remove the https:// (https:// as you can see is 8 characters so we cuttof the first 8 characters)
    elif(url.startswith('http://')):
        #set the port to 80 IF it starts with http://
        port = 80
        protocol = 'http'
        url = url[7:]
    else:
        return None, None, None, None
    
    #this finds the start of the index where the path starts
    slash_index = url.find('/')

    #means that there is no path
    if(slash_index == -1):
        host = url
        path ='/'
    else:
        #means we found a path, therefore we split accordingly
        host = url[:slash_index]
        path = url[slash_index:]


    #we return the necessary things needed when parsing the url
    return host, protocol, port, path


#------Network Functions------
def establish_connection(host, port, protocol):
    #This function creates and connects the socket with the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    sock.connect((host, port)) # May raise a network error

    # Handle HTTPS (Extra Credit)
    if protocol == 'https':
        #if the protocol starts with https (we use ssl to secure security)
        #https differs from http in the way that https is supposed to keep user info secure while http does not
        #that is why we check for https and then use ssl
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)
    
    return sock

def send_request(sock, host, path):
    #constructs and sends the http/1.0 request
    request = f'GET {path} HTTP/1.0\r\n'
    request += f'Host: {host}\r\n'
    request += '\r\n'
    sock.sendall(bytes(request, 'utf-8'))

def receive_response(sock):
    #receives the complete HTTP response from the server
    response = b''
    while True:
        data = sock.recv(4096)
        if not data:
            break
        response+=data

    return response


#------Logic Functions-------
def follow_redirection(original_url, headers_text):
    #This function is called if the URL is redirected, meaning if you get a code between 300 and 400 meaning the url is redirected but not an error
    location_match = re.search(r'Location: (.*?)\r\n', headers_text, re.IGNORECASE)
    
    if location_match:
        redirected_url = location_match.group(1).strip()
        print(f"Redirected URL: {redirected_url}")
        
        fetch_url(redirected_url, is_redirected=True)
    else:
        print("Status: 3XX Redirection Failure (No Location header)")

def fetch_referenced_objects(original_url, response_body):
    #This checks if the images inside of the url are also being rendered, making sure that the images also render and not just the page
    image_srcs = re.findall(r'<img\s+[^>]*src\s*=\s*["\']?([^"\'\s>]+)["\'\s>]', response_body, re.IGNORECASE)
    
    host, protocol, port, _ = parse_url(original_url)
    base_url = f"{protocol}://{host}"
    
    for src in image_srcs:
        image_url = src

        if src.startswith('//'):
            image_url = f"{protocol}:{src}"
        elif src.startswith('/'):
            image_url = f"{base_url}{src}"
        
        if image_url.startswith('http'):
            fetch_url(image_url, is_referenced=True)

def analyze_response(url, response_data):    
    #This parses and interprets the HTTP response and returns the correct status code given
    if not response_data:
        print("Status: Network Error (Empty Response)")
        return

    response_text = response_data.decode('latin-1')
    header_body_split = response_text.split('\r\n\r\n', 1)
    headers_text = header_body_split[0]
    body_text = header_body_split[1] if len(header_body_split) > 1 else ""

    status_line = headers_text.split('\r\n')[0]
    
    try:
        status_parts = status_line.split()
        status_code = int(status_parts[1])
        status_phrase = ' '.join(status_parts[2:])
        
        print(f"Status: {status_code} {status_phrase}")
    except:
        print("Status: Network Error (Invalid Response Format)")
        return

    if 300 <= status_code < 400:
        follow_redirection(url, headers_text)
        return

    if 200 <= status_code < 300:
        fetch_referenced_objects(url, body_text)
        return
    

#-------Fetching Functions------
def fetch_url(url, is_redirected=False, is_referenced=False):
    #this fetches the URL and creates the sockets and connects them with the Server
    host, protocol, port, path = parse_url(url)

    if not host: 
        print(f"Url: [{url}] is invalid")
        return
    
    if is_referenced:
        print(f"Referenced URL: {url}")
    elif not is_redirected:
        print(f"URL: {url}")

    sock = None
    response_data = None

    try:
        sock = establish_connection(host, port, protocol)
        send_request(sock, host, path)
        response_data = receive_response(sock)
        analyze_response(url, response_data)
    except Exception as e:
        print("Status: Network error")
        return
    
    finally:
        if sock:
            sock.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: monitor urls_file')
        sys.exit(1)
        
    urls_file_name = sys.argv[1]
    urls = []

    #Parses through the txt file and extracts the url's
    try:
        with open(urls_file_name, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: URLs file '{urls_file_name}' not found.")
        sys.exit(1)

    #Calls the fetch_url(url) function and passes the url in urls array into it
    for url in urls:
        fetch_url(url)