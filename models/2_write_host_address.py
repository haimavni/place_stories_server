import os

def __get_host_address():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    fname = 'host_address.txt'
    file_path = os.path.join(base_path, fname)
    
    if not os.path.exists(file_path):
        host_address = request.env.http_origin or ('http://' + request.env.http_host)
        if host_address:
            with open(file_path, 'w') as f:
                f.write(host_address)
    
    host_adress = 'missing host address'
    if os.path.exists(file_path):
        with open(file_path) as f:
            host_address = f.read().strip()
            
    return host_address

__get_host_address()