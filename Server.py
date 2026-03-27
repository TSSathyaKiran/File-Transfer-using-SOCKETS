import socket
import os
import hashlib
import json
import time

PORT = 5001
ADDR = '127.0.0.1'
file_name = "luffy.jpg"
CHUNK_SIZE = 4096
TIMEOUT = 5

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((ADDR, PORT))
server.settimeout(TIMEOUT)
print(f"Listening on {ADDR}:{PORT}")

try:
    data, client_addr = server.recvfrom(1024)
    print(f"Client connected from {client_addr}")
    
    file_size = os.path.getsize(file_name)
    with open(file_name, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    metadata = {
        'filename': file_name,
        'size': file_size,
        'hash': file_hash,
        'chunk_size': CHUNK_SIZE
    }
    server.sendto(json.dumps(metadata).encode('utf-8'), client_addr)
    
    with open(file_name, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            msg = {
                'chunk_num': chunk_num,
                'data': chunk.hex()
            }
            server.sendto(json.dumps(msg).encode('utf-8'), client_addr)
            
            try:
                ack, _ = server.recvfrom(1024)
                ack_data = json.loads(ack.decode('utf-8'))
                if ack_data['chunk_num'] == chunk_num:
                    print(f"Chunk {chunk_num} sent and acknowledged")
            except socket.timeout:
                print(f"Timeout on chunk {chunk_num}, resending...")
                pass
            
            chunk_num += 1
    
    final_msg = json.dumps({'chunk_num': -1, 'data': ''}).encode('utf-8')
    server.sendto(final_msg, client_addr)
    
    print("File transfer complete")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    server.close()