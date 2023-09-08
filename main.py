import bencodepy
import socket
import hashlib
import os
import concurrent.futures
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.settimeout(2)
info_hash_hex = '443c7602b4fde83d1154d6d9da48808418b181b6'
def random_node_id(size=20):
    m = hashlib.sha1()
    m.update(os.urandom(20))
    m = m.digest()
    return m

def decodeaddr(addr):
    nid = addr[:20]
    ip = socket.inet_ntoa(addr[20:24])
    port = int.from_bytes(addr[24:26], 'big')
    return (nid, ip, port)
info_hash = bytes.fromhex(info_hash_hex)

self_node_id = random_node_id(20)

dht_bootstraps =[
        ('router.bittorrent.com', 6881),
        #('router.utorrent.com',6881),
        #('router.bitcomet.com',6881),
        #('dht.transmissionbt.com',6881),
        #('dht.aelitis.com',6881)
    ]
def send_krpc(node_ip, node_port, krpc):
    try:
        print(f"Sending {krpc} to: {node_ip, node_port}")
        UDPClientSocket.sendto(bencodepy.encode(krpc), (node_ip, node_port))
        msgFromServer, addr = UDPClientSocket.recvfrom(2048)
        print(f"Received message: {bencodepy.decode(msgFromServer)}")
        sanitized_response=sanitze_response(msgFromServer)
        peers=check_peers(msgFromServer)
        if peers!=None:
            for peer in peers: 
                ip=str(socket.inet_ntoa(peer[0:4])) 
                port=str(int.from_bytes(peer[4:6], 'big'))
                with open(f'{info_hash_hex}.txt', 'a+') as f:
                    if f'{ip}:{port}' in f.read().split('\n'):
                        continue
                    else:
                        with open(f'{info_hash_hex}.txt', 'a') as f:
                            f.write(f'{ip}:{port}' )
                            f.write('\n')

        print(f"Sanitized response: {sanitized_response}")
        return sanitized_response
    except TimeoutError:
        print("Timeout")

BUCKET=[]
def check_peers(msgFromServer):
    try:
        if bencodepy.decode(msgFromServer)[b'r'][b'values']==[]:
            return None
        else:
            return bencodepy.decode(msgFromServer)[b'r'][b'values']
    except:
        return None
    
def sanitze_response(msgFromServer):
    bucket=[]
    try:
        nodes = bencodepy.decode(msgFromServer)[b'r'][b'nodes']
        for i in range(0, len(nodes), 26):
            node = nodes[i:i+26]
            nid, ip, port =  decodeaddr(node)
            bucket.append([nid, ip, port])
        return bucket
    except KeyError:
        return []
    
def crawl_dht():
    krpc = {"t": b"ea", "y": "q", "q": "get_peers", "a": {"id": self_node_id, "info_hash":info_hash}}
    for node in dht_bootstraps:
        print(node)
        UDPClientSocket.sendto(bencodepy.encode(krpc), node)
        msgFromServer, addr = UDPClientSocket.recvfrom(2048)
        print(bencodepy.decode(msgFromServer))
        sanitized_response  =sanitze_response(msgFromServer)
        print(sanitized_response)
        for node in sanitized_response:
            print("node")
            print(node)
            BUCKET.append(node)

    
    krpc = {"t": b"ea", "y": "q", "q": "get_peers", "a": {"id": self_node_id, "info_hash":info_hash}}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            for node in BUCKET:
                ip = node[1]
                port = node[2]
                future = executor.submit(send_krpc,ip, port, krpc)
            if future.result() == [] or future.result() == None:
                continue
            else:
                print((future.result()))
                for node in future.result():
                    if node not in BUCKET:
                        BUCKET.append(node)

            print('lenth of bucket', len(BUCKET))
            


crawl_dht()
