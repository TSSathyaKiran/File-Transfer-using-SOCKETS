import socket
import json
import hashlib
import os

ADDR = '127.0.0.1'
PORT = 5001
TIMEOUT = 5

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(TIMEOUT)
print("Connecting to server...")

try:
    client.sendto(b'HELLO', (ADDR, PORT))
    
    metadata_msg, server_addr = client.recvfrom(4096)
    metadata = json.loads(metadata_msg.decode('utf-8'))
    
    filename = metadata['filename']
    file_size = metadata['size']
    expected_hash = metadata['hash']
    chunk_size = metadata['chunk_size']
    
    print(f"Receiving: {filename} ({file_size} bytes)")
    
    output_filename = f"Received_{filename}"
    
    received_chunks = {}
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    
    if os.path.exists(output_filename):
        with open(output_filename, 'rb') as f:
            partial_data = f.read()
        received_size = len(partial_data)
        print(f"Resuming from {received_size} bytes")
    else:
        partial_data = b''
    
    with open(output_filename, 'wb') as f:
        f.write(partial_data)
    
    while True:
        try:
            chunk_msg, _ = client.recvfrom(4096 + 512)
            chunk_data = json.loads(chunk_msg.decode('utf-8'))
            chunk_num = chunk_data['chunk_num']
            
            if chunk_num == -1:
                print("Transfer complete")
                break
            
            data = bytes.fromhex(chunk_data['data'])
            received_chunks[chunk_num] = data
            
            with open(output_filename, 'ab') as f:
                f.write(data)
            
            ack = json.dumps({'chunk_num': chunk_num}).encode('utf-8')
            client.sendto(ack, server_addr)
            print(f"Received chunk {chunk_num}")
            
        except socket.timeout:
            print("Timeout waiting for chunk")
            break
    
    with open(output_filename, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    if file_hash == expected_hash:
        print("Integrity check passed")
    else:
        print(f"Integrity check failed! Expected {expected_hash}, got {file_hash}")
    
    print(f"File saved as {output_filename}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
