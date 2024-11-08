
from asyncio import Task
import asyncio
from base64 import b64encode
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4
from httpx import AsyncClient

from data import DataType
from heapq import heappop, heappush
from functools import total_ordering
from datetime import datetime

@total_ordering
class CatatanStream:

    def __init__(self, url: str):
        self.url: str = url
        self.client: AsyncClient | None = None

        self.process: int = 0
        self.total_data: int = 0
        self.content_type: DataType | None = None 

    async def connect(self):
        assert self.client is None, "Client already initialized"

        self.client = AsyncClient()
    
    async def get_data(self) -> AsyncGenerator[bytes, Any]:
    
        assert self.client is not None, "Client already initialized"

        async with self.client.stream("GET", self.url) as stream:

            content_type: str = stream.headers.get("Content-Type")
            content_length: int = int(stream.headers.get("Content-Length"))

            # TODO: fix this later by adding a proper API design
            # TODO: handle error when fialure happens

            self.content_type = DataType.parse(content_type)
            self.total_data = content_length

            # allowing fetching the header only first
            yield b''

            async for data in stream.aiter_bytes():
                self.process += len(data)
                print(f"Current progress: {(self.process/self.total_data) * 100 }%")
                yield data
        
    async def disconnect(self):
        assert self.client != None, "Client should not be empty"
        await self.client.aclose()

    def __lt__(self, other: 'CatatanStream'):
        return self.total_data < other.total_data


class CatatanDownloadScheduler:
    #TODO: ADD METRIC SUCH AS AVERAGE TURNAROUND

    UNIQUE_ID_LENGTH: int = 8
    
    def __init__(self, max_concurrent_download: int, max_connection: int):
        self.max_concurrent_download: int = max_concurrent_download
        self.max_connection: int = max_connection

        self.downloading_tasks: list[Task[Any]] = []
        self.pending_download_tasks: list[CatatanStream] = []
        self.start_task: Task[Any] | None = None

    def __call__(self):
        self.start_task = asyncio.create_task(self.__start())

    def __del__(self) -> bool:
        assert self.start_task != None
        return self.start_task.cancel()

    async def add_donwload_task(self, url: str):
        #TODO: CHECK THE LENGTH USING LOCK
        if len(self.pending_download_tasks) >= self.max_connection:
            raise Exception("Cannot addd more url, exceeding max_connection")

        new_stream = CatatanStream(url)
        await new_stream.connect()
        _ = await anext(new_stream.get_data())

        heappush(self.pending_download_tasks, new_stream)

    async def __download(self, stream: CatatanStream, task_name: str):
        assert stream.content_type != None

        file_name = b64encode((stream.url + str(uuid4())[:CatatanDownloadScheduler.UNIQUE_ID_LENGTH]).encode()).decode() + stream.content_type.get_file_extension()

        with open(file_name, 'wb+') as file:
            async for data in stream.get_data():
                _ = file.write(data)
        
        for task in self.downloading_tasks:
            if task.get_name() == task_name:
                #TODO: use asyncio lock
                self.downloading_tasks.remove(task)
                break

        await stream.disconnect()

    async def __start(self):

        while True:
            if len(self.pending_download_tasks) > 0 and len(self.downloading_tasks) < self.max_concurrent_download:
                smallest_stream = heappop(self.pending_download_tasks)
                task_name = (smallest_stream.url + str(datetime.now()))
                task = asyncio.create_task(self.__download(smallest_stream, task_name), name=task_name)
                self.downloading_tasks.append(task)
