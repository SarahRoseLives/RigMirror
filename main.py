import asyncio


class AsyncRigControlServer:
    def __init__(self, primary_ip, primary_port, secondary_ip, secondary_port):
        # Initialize server with IP addresses and ports for primary and secondary radios
        self.primary_ip = primary_ip
        self.primary_port = primary_port
        self.secondary_ip = secondary_ip
        self.secondary_port = secondary_port
        self.running = False  # Flag to control the server's running state
        self.last_frequency = None  # Store the last read frequency for comparison

    async def open_connections(self):
        """Open TCP connections to both radios."""
        self.primary_reader, self.primary_writer = await asyncio.open_connection(self.primary_ip, self.primary_port)
        print(f"Connected to primary radio at {self.primary_ip}:{self.primary_port}")

        self.secondary_reader, self.secondary_writer = await asyncio.open_connection(self.secondary_ip, self.secondary_port)
        print(f"Connected to secondary radio at {self.secondary_ip}:{self.secondary_port}")

    async def close_connections(self):
        """Close TCP connections to both radios."""
        self.primary_writer.close()
        await self.primary_writer.wait_closed()
        print("Closed connection to primary radio.")

        self.secondary_writer.close()
        await self.secondary_writer.wait_closed()
        print("Closed connection to secondary radio.")

    async def get_rig_data(self, command, reader, writer):
        """Send a command to a rig and receive the response."""
        writer.write(command.encode('utf-8'))
        await writer.drain()
        response = await reader.read(1024)
        response = response.decode('utf-8').strip()
        print(f"Received response: {response}")
        return response

    async def read_frequency(self):
        """Read frequency from the primary radio using the correct command."""
        return await self.get_rig_data('f\n', self.primary_reader, self.primary_writer)

    async def set_frequency(self, frequency):
        """Set frequency on the secondary radio."""
        command = f'F {frequency}\n'  # Command to set frequency, adjust as needed
        self.secondary_writer.write(command.encode('utf-8'))
        await self.secondary_writer.drain()
        response = await self.secondary_reader.read(1024)
        response = response.decode('utf-8').strip()
        print(f"Set frequency on secondary radio to: {frequency}")
        print(f"Response from secondary radio after setting frequency: {response}")

    async def sync_frequencies(self):
        """Continuously synchronize the frequency from the primary to the secondary radio."""
        while self.running:
            freq = await self.read_frequency()
            if freq and freq != self.last_frequency:
                print(f"Frequency changed: {self.last_frequency} -> {freq}")
                await self.set_frequency(freq)
                self.last_frequency = freq
            await asyncio.sleep(0.1)  # Adjust the sync interval as needed

    async def start(self):
        """Start the rig control server."""
        await self.open_connections()
        self.running = True
        await self.sync_frequencies()

    async def stop(self):
        """Stop the rig control server."""
        self.running = False
        await self.close_connections()


if __name__ == '__main__':
    # Configuration for the primary and secondary radios
    primary_ip = 'localhost'  # Replace with your primary radio's IP address
    primary_port = 4532  # Replace with your primary radio's port
    secondary_ip = 'localhost'  # Replace with your secondary radio's IP address
    secondary_port = 4533  # Replace with your secondary radio's port

    server = AsyncRigControlServer(primary_ip, primary_port, secondary_ip, secondary_port)
    try:
        # Run the server
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Stopping Rig Control Server.")
        # Ensure server is properly stopped
        asyncio.run(server.stop())
