# FastAPI Application Architecture

Complete guide to understanding how FastAPI, uvloop, uvicorn, and your application work together.

---

## Table of Contents

1. [Overview](#overview)
2. [Component Responsibilities](#component-responsibilities)
3. [Startup Sequence](#startup-sequence)
4. [Request Processing Flow](#request-processing-flow)
5. [Async vs Sync Execution](#async-vs-sync-execution)
6. [The Event Loop (uvloop)](#the-event-loop-uvloop)
7. [Database Connection Flow](#database-connection-flow)

---

## Overview

When you run `uvicorn app.main:app`, you spawn a **single Python process** that initializes multiple modules working together. **uvloop** is the "heart" that stays on stand-by, waiting for OS events.

### The Stack

```
┌─────────────────────────────────────────────────────┐
│  Python Process                                     │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ uvloop (THE TRIGGERER)                        │ │
│  │ - Infinite event loop                         │ │
│  │ - Waiting on epoll for OS events              │ │
│  │ - "Standing by" consuming 0% CPU              │ │
│  └─────────────────┬─────────────────────────────┘ │
│                    │                                │
│                    ↓ OS event arrives               │
│  ┌───────────────────────────────────────────────┐ │
│  │ uvicorn (THE COORDINATOR)                     │ │
│  │ - Accepts connections                         │ │
│  │ - Reads raw bytes                             │ │
│  │ - Calls httptools                             │ │
│  └─────────────────┬─────────────────────────────┘ │
│                    │                                │
│                    ↓ Raw HTTP bytes                 │
│  ┌───────────────────────────────────────────────┐ │
│  │ httptools (THE PARSER)                        │ │
│  │ - Parses HTTP syntax                          │ │
│  │ - Extracts method, path, headers              │ │
│  └─────────────────┬─────────────────────────────┘ │
│                    │                                │
│                    ↓ Parsed request object          │
│  ┌───────────────────────────────────────────────┐ │
│  │ FastAPI (THE ROUTER)                          │ │
│  │ - Routes to correct endpoint                  │ │
│  │ - Decides async vs sync execution             │ │
│  │ - Handles dependency injection                │ │
│  └─────────────────┬─────────────────────────────┘ │
│                    │                                │
│                    ↓                                │
│  ┌───────────────────────────────────────────────┐ │
│  │ Your Application Code                         │ │
│  │ - Business logic                              │ │
│  │ - Database queries                            │ │
│  │ - Response generation                         │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### uvloop - The Event Loop Engine

**What it does:**
- Runs an infinite loop waiting for OS events
- Uses `epoll` (Linux) or `kqueue` (macOS) system calls
- Wakes up when events occur (new connections, data arrives, timers expire)
- Schedules async tasks

**What it does NOT do:**
- Parse HTTP
- Route requests
- Manage your application logic

**Code equivalent:**
```python
while True:  # Infinite loop
    events = epoll.wait()  # ← BLOCKS here waiting for OS
    
    for event in events:
        if event.type == "socket_readable":
            # Wake up and notify uvicorn
            handle_event(event)
```

---

### uvicorn - The Coordinator

**What it does:**
- Creates and manages the server socket (port 8000)
- Accepts incoming TCP connections
- Reads raw bytes from socket
- Calls httptools to parse HTTP
- Passes parsed requests to FastAPI
- Sends responses back to clients

**What it does NOT do:**
- Manage the event loop (delegates to uvloop)
- Parse HTTP itself (delegates to httptools)
- Route requests (delegates to FastAPI)

**Code equivalent:**
```python
async def serve():
    # Create listening socket
    server_socket = socket.socket()
    server_socket.bind(("0.0.0.0", 8000))
    server_socket.listen()
    
    while True:
        # Wait for connection (uvloop handles the waiting)
        connection, address = await server_socket.accept()
        
        # Read data
        data = await connection.read()
        
        # Parse HTTP
        request = httptools.parse(data)
        
        # Call FastAPI
        response = await app(request)
        
        # Send response
        await connection.write(response)
```

---

### httptools - The HTTP Parser

**What it does:**
- Parses raw HTTP bytes
- Extracts method, path, headers, body
- Returns a structured request object

**What it does NOT do:**
- Manage connections
- Route requests
- Know anything about your application

**Code equivalent:**
```python
def parse(raw_bytes):
    # Input: b"GET /api/v1/games HTTP/1.1\r\nHost: localhost\r\n\r\n"
    # Output: Request(method="GET", path="/api/v1/games", ...)
    
    method = extract_method(raw_bytes)
    path = extract_path(raw_bytes)
    headers = extract_headers(raw_bytes)
    body = extract_body(raw_bytes)
    
    return Request(method, path, headers, body)
```

---

### FastAPI - The Router & Decision Maker

**What it does:**
- Matches request path to endpoint handler
- Inspects function signature (`async def` vs `def`)
- Decides execution context (event loop vs thread pool)
- Handles dependency injection
- Validates request/response with Pydantic

**What it does NOT do:**
- Parse HTTP (delegates to httptools via uvicorn)
- Manage the event loop (uses asyncio/uvloop)

**Code equivalent:**
```python
async def handle_request(request):
    # Find route
    route = router.match(request.path)
    handler = route.endpoint
    
    # Inspect function
    if inspect.iscoroutinefunction(handler):
        # It's async def - run on event loop
        response = await handler(request)
    else:
        # It's def - run in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, handler, request)
    
    return response
```

---

## Startup Sequence

When you run `uvicorn app.main:app`:

```
┌─────────────────────────────────────────────┐
│ 1. Python Interpreter Starts               │
│    Single process created                   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 2. Import uvicorn                           │
│    Python code that coordinates everything  │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 3. Import and Install uvloop                │
│    C extension for fast event loop          │
│    asyncio.set_event_loop_policy(uvloop)    │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 4. Import app.main                          │
│    - Imports FastAPI                        │
│    - Imports SQLAlchemy (database.py)       │
│    - Creates database engine/pool           │
│    - Creates FastAPI() instance             │
│    - Registers all routes                   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 5. Run Lifespan Startup                     │
│    - init_db() creates database tables      │
│    - Any other startup tasks                │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 6. uvicorn.run(app)                         │
│    - Creates server socket                  │
│    - Binds to 0.0.0.0:8000                  │
│    - Starts listening                       │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 7. uvloop.run_forever()                     │
│                                             │
│    while True:                              │
│        events = epoll.wait()  ← HERE!       │
│                                             │
│    Process is now "standing by"             │
│    Consuming near 0% CPU                    │
│    Waiting for OS events...                 │
└─────────────────────────────────────────────┘
```

**Terminal Output:**
```bash
$ uvicorn app.main:app --reload
🚀 Starting up...
📊 Initializing database...
✅ Database initialized!
INFO:     Uvicorn running on http://0.0.0.0:8000

  ← Process is here, in uvloop's infinite loop
     Standing by for requests...
```

---

## Request Processing Flow

### Complete Flow: HTTP Request → Response

```
┌─────────────────────────────────────────────┐
│ 1. Browser sends HTTP request               │
│    GET /api/v1/games HTTP/1.1               │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 2. OS Kernel receives TCP packet            │
│    Network card → TCP/IP stack → Socket     │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 3. epoll notifies uvloop                    │
│    "Socket 42 is readable!"                 │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 4. uvloop wakes from epoll.wait()           │
│    Event loop unblocks                      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 5. uvicorn accepts connection               │
│    connection, addr = await socket.accept() │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 6. uvicorn reads raw bytes                  │
│    data = await connection.recv()           │
│    data = b"GET /api/v1/games HTTP/1.1..."  │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 7. httptools parses HTTP                    │
│    request = httptools.parse(data)          │
│    request.path = "/api/v1/games"           │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 8. FastAPI route matching                   │
│    router.match("/api/v1/games")            │
│    Found: get_games() function              │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 9. FastAPI inspects function                │
│    Is it async def or def?                  │
│    ✓ async def get_games(...)               │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 10. FastAPI injects dependencies            │
│     db = await get_db()  # New session      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 11. Execute endpoint on event loop          │
│     result = await get_games(db)            │
│     - Query database (async)                │
│     - Business logic                        │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 12. Return response                         │
│     return {"games": [...]}                 │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 13. uvicorn sends HTTP response             │
│     await connection.send(response_bytes)   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 14. Browser receives response               │
│     { "games": [...] }                      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ 15. Back to uvloop event loop               │
│     Loop continues, waiting for next event  │
└─────────────────────────────────────────────┘
```

---

## Async vs Sync Execution

### Async Endpoint (Event Loop)

```python
@router.get("/games")
async def get_games(db: DatabaseSession):
    result = await db.execute(select(BoardGame))
    return result.scalars().all()
```

**Execution:**
```
Request arrives
    ↓
FastAPI sees: async def
    ↓
Run on EVENT LOOP (same thread as uvloop)
    ↓
await db.execute() → yields control
    ↓
Event loop handles OTHER requests while waiting
    ↓
Database responds → resume this task
    ↓
Return response
```

**Benefits:**
- ✅ Single thread handles 1000+ concurrent requests
- ✅ Very efficient for I/O-bound operations
- ✅ No thread overhead

---

### Sync Endpoint (Thread Pool)

```python
@router.get("/sync-games")
def get_sync_games():
    result = requests.get("https://...")  # Blocking!
    return result.json()
```

**Execution:**
```
Request arrives
    ↓
FastAPI sees: def (not async)
    ↓
Submit to THREAD POOL
    ↓
ThreadPoolExecutor assigns to worker thread
    ↓
Thread BLOCKS on requests.get()
    ↓
Event loop continues handling OTHER requests
    ↓
Thread finishes → event loop resumes
    ↓
Return response
```

**When to use:**
- CPU-bound operations
- Blocking libraries without async support
- Legacy code

**Thread Pool Manager:** `ThreadPoolExecutor` from `concurrent.futures`
- Default: 40 threads
- Shared across all sync endpoints

---

## The Event Loop (uvloop)

### What is uvloop?

uvloop is a **drop-in replacement** for Python's asyncio event loop, written in Cython and wrapping libuv (the same C library used by Node.js).

### Architecture

```
┌─────────────────────────────────────────────┐
│  uvloop (Cython - Python → C)               │
│  - High-level async/await interface         │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  libuv (C library)                          │
│  - Cross-platform async I/O                 │
│  - Event loop implementation                │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  OS System Calls                            │
│  - Linux: epoll                             │
│  - macOS: kqueue                            │
│  - Windows: IOCP                            │
└─────────────────────────────────────────────┘
```

### The Infinite Loop

```python
# Simplified version of what uvloop does:

while True:  # Infinite loop - never exits!
    # 1. Wait for OS events (this is a blocking system call)
    events = epoll.wait(timeout=None)  # ← Process "sleeps" here
    
    # 2. OS wakes us up when event arrives
    # (new connection, data ready, timer expired, etc.)
    
    # 3. Process each event
    for event in events:
        if event.type == SOCKET_READABLE:
            # Socket has data - call the registered callback
            callback = callbacks[event.fd]
            callback(event.fd)
        
        elif event.type == TIMER_EXPIRED:
            # Timer expired - run the scheduled task
            scheduled_task.execute()
    
    # 4. Run any pending async tasks
    run_pending_tasks()
    
    # 5. Loop back to step 1 (wait for more events)
```

### Why It's Efficient

**CPU Usage:**
- When waiting: **0% CPU** (process is blocked in kernel)
- When processing: Bursts of activity, then back to 0%

**Memory Usage:**
- Single thread: ~1MB stack
- vs 100 threads: ~100MB stacks

**Event Handling:**
- Can monitor thousands of sockets simultaneously
- OS notifies only when something actually happens
- No busy-waiting or polling

---

## Database Connection Flow

### Connection Hierarchy

```
Your Endpoint Code
    ↓
┌─────────────────────────────────────────────┐
│ DatabaseSession (SQLAlchemy AsyncSession)   │
│ - Tracks pending changes                    │
│ - Identity map (object cache)               │
│ - Transaction state                         │
│ Lifespan: One per request                   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Connection (from connection pool)           │
│ - Physical TCP connection to PostgreSQL     │
│ - PostgreSQL wire protocol state            │
│ Pool size: 5 connections (default)          │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ asyncpg Driver                              │
│ - Async PostgreSQL driver                   │
│ - Integrates with uvloop event loop         │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ TCP Socket (e.g., localhost:5432)           │
│ - OS-level socket connection                │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ PostgreSQL Server                           │
└─────────────────────────────────────────────┘
```

### How Database Queries Work

```python
@router.get("/games")
async def get_games(db: DatabaseSession):
    # Step 1: FastAPI calls get_db()
    # - Creates new AsyncSession from pool
    # - Gets a connection from connection pool (or creates one)
    
    # Step 2: Execute query
    result = await db.execute(select(BoardGame))
    
    # What happens at 'await':
    # 1. asyncpg sends SQL to PostgreSQL (via TCP socket)
    # 2. asyncpg registers interest with uvloop: "notify me when socket is readable"
    # 3. Event loop YIELDS - can handle other requests now!
    # 4. PostgreSQL processes query
    # 5. PostgreSQL sends response
    # 6. OS notifies uvloop: "socket is readable"
    # 7. uvloop wakes up this task
    # 8. asyncpg reads response from socket
    # 9. Task continues executing
    
    # Step 3: Process results
    games = result.scalars().all()
    
    # Step 4: Return response
    return games
    
    # Step 5: FastAPI cleanup
    # - Session is closed (automatic via get_db)
    # - Connection returned to pool
```

### Connection Pool Benefits

**Without pooling:**
- Every request creates new connection: SLOW (TCP handshake + auth)
- 100 requests = 100 connections

**With pooling (our setup):**
- 5 connections created at startup
- Reused across requests: FAST
- 100 requests = 5 connections (reused)

---

## Key Takeaways

### 1. Single Process Architecture
Everything runs in **one Python process**:
- uvloop
- uvicorn
- FastAPI
- Your application code
- Database connection pool
- Thread pool (for sync endpoints)

### 2. uvloop is the Foundation
- Runs the infinite event loop
- Waits on OS events (epoll/kqueue)
- Triggers the entire request chain
- Never exits (until Ctrl+C)

### 3. Async Means Cooperative
- Not about parallelism (that's threading/multiprocessing)
- About efficient I/O handling
- Single thread switches between tasks at `await` points

### 4. The Chain of Command
```
uvloop → uvicorn → httptools → FastAPI → Your Code
```

Each layer has a specific job. They work together but are independent.

### 5. Database Connections are Async Too
- asyncpg integrates with uvloop
- `await db.execute()` = non-blocking database query
- Connection pool shared across all requests

---

## Performance Characteristics

### Async Endpoint
- **Concurrency:** 1000+ requests per thread
- **Memory:** ~1MB per thread
- **CPU:** Efficient (event-driven)
- **Best for:** Database queries, API calls, I/O operations

### Sync Endpoint
- **Concurrency:** 40 requests (default thread pool size)
- **Memory:** ~40MB for thread stacks
- **CPU:** Context switching overhead
- **Best for:** CPU-bound work, blocking libraries

### Connection Pool
- **Pool size:** 5 connections (default)
- **Max overflow:** 10 additional connections
- **Total capacity:** 15 simultaneous database operations
- **Reuse:** Connections shared across thousands of requests

---

## Summary

When you run your FastAPI application:

1. **One Python process** is created
2. **uvloop** enters an infinite loop, waiting on OS events
3. When HTTP request arrives, **OS notifies uvloop**
4. **uvloop triggers uvicorn** to accept connection
5. **uvicorn reads bytes** and calls **httptools** to parse
6. **httptools returns parsed request** to uvicorn
7. **uvicorn passes to FastAPI** for routing
8. **FastAPI inspects your function** and decides execution context
9. **Your code executes** (on event loop or thread pool)
10. **Response flows back** through the stack
11. **uvloop continues** waiting for next event

This architecture enables **high concurrency** with **low resource usage** - perfect for web APIs! 🚀
