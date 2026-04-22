import asyncio
import socket
import uselect
import domo_utils as d_u

class DNSServer:
    def __init__(self, ip):
        self.ip = ip
        self.port = 53
        self._poll = uselect.poll()

    async def start(self):
        d_u.print_and_store_log("Starting DNS Server (Captive Portal) on port 53...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(('0.0.0.0', self.port))
        self._poll.register(self.sock, uselect.POLLIN)
        
        while True:
            try:
                # Basic non-blocking receive
                data, addr = await self._recv_from()
                if data:
                    response = self._process_query(data)
                    if response:
                        self.sock.sendto(response, addr)
            except Exception as e:
                await asyncio.sleep(0.1)
            await asyncio.sleep(0)

    async def _recv_from(self):
        # Wait for data using pre-initialized poll
        if self._poll.poll(100):
            return self.sock.recvfrom(512)
        return None, None

    def _process_query(self, data):
        if len(data) < 12:
            return None
        # Transaction ID
        packet = data[:2]
        # Flags: Standard query response, No error
        packet += b'\x81\x80'
        # Questions and Answer Counts
        packet += data[4:6] + data[4:6] + b'\x00\x00\x00\x00'
        
        # Original Question: find the end of the labels (null byte)
        query_end = 12
        while query_end < len(data) and data[query_end] != 0:
            query_end += data[query_end] + 1
        query_end += 5 # Null byte + Type (2) + Class (2)
        
        if query_end > len(data):
            return None
            
        packet += data[12:query_end]
        # Answer: Name Pointer (0xc00c), Type A, Class IN, TTL 60s, Length 4, IP
        packet += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
        packet += bytes(map(int, self.ip.split('.')))
        return packet

async def run_dns(ip):
    dns = DNSServer(ip)
    await dns.start()
