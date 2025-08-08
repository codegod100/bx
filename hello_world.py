from puepy import Application, Page, t
from puepy.router import Router
import pyscript
from js import window
import asyncio
import json
import time

print("[STARTUP] hello_world.py loaded, initializing application...")

# Custom error page that handles None errors better
class CustomErrorPage(Page):
    props = ["error"]

    def populate(self):
        t.h1("Application Error", class_name="text-3xl font-bold mb-6 text-center text-red-500")
        if self.error:
            t.p(f"Error: {str(self.error)}", class_name="mb-4")
            t.pre(str(self.error), class_name="bg-gray-100 p-4 rounded")
        else:
            t.p("An unknown error occurred.", class_name="mb-4")
            t.p("Please check the browser console for more details.", class_name="mb-4")

# Determine base path based on environment
# Check if we're on GitHub Pages (or similar platform with subpath deployment)
base_path = ""
try:
    # If the current path contains a subpath that's not just "/", we might be in a subfolder deployment
    # This works for GitHub Pages where repos are served at username.github.io/repo-name
    if window.location.pathname.count("/") > 1:
        # Extract the first path segment as the base path
        path_parts = window.location.pathname.split("/")
        if len(path_parts) > 1 and path_parts[1]:
            base_path = "/" + path_parts[1]
except:
    pass

app = Application()
app.error_page = CustomErrorPage
app.install_router(Router, base_path=base_path, link_mode=Router.LINK_MODE_HTML5)


@app.page()
class HelloWorldPage(Page):
    def initial(self):
        # Try to hydrate from OPFS-provided initial state
        print("[INIT] Initializing page state...")
        try:
            import json
            raw = window.__INITIAL_STATE__
            print(f"[INIT] Raw initial state: {raw}")
            if raw is not None:
                # Handle both JsProxy with to_py() and plain Python str
                try:
                    raw_str = raw.to_py() if hasattr(raw, "to_py") else raw
                except Exception:
                    raw_str = raw
                if isinstance(raw_str, bytes):
                    raw_str = raw_str.decode("utf-8")
                if isinstance(raw_str, str) and len(raw_str) > 0:
                    data = json.loads(raw_str)
                    if isinstance(data, dict):
                        defaults = {
                            "count": 0,
                            "input_text": "",
                            "todos": [],
                            "completed": [],
                            "stream_data": [],
                            "is_connected": False,
                            "connection_status": "Disconnected"
                        }
                        defaults.update({k: v for k, v in data.items() if k in defaults})
                        print(f"[INIT] Loaded state from OPFS: {len(defaults)} properties")
                        return defaults
        except Exception as e:
            print(f"[INIT] Failed to load OPFS state: {e}")
        print("[INIT] Using default initial state")
        return {
            "count": 0,
            "input_text": "",
            "todos": [],
            "completed": [],
            "stream_data": [],
            "is_connected": False,
            "connection_status": "Disconnected"
        }
    
    def on_mount(self):
        """Called when the page is mounted - auto-connect to stream"""
        print("[MOUNT] Page mounted (on_mount), initializing stream connection...")
        # Enable auto-reconnect loop and start
        self._stream_should_run = True
        print("[MOUNT] Stream enabled, calling auto_connect_stream()")
        self.auto_connect_stream()
    
    def mounted(self):
        """Alternative lifecycle method name - auto-connect to stream"""
        print("[MOUNT] Page mounted (mounted), initializing stream connection...")
        # Enable auto-reconnect loop and start
        self._stream_should_run = True
        print("[MOUNT] Stream enabled, calling auto_connect_stream()")
        self.auto_connect_stream()
    
    def on_ready(self):
        """Another possible lifecycle method name"""
        print("[MOUNT] Page ready (on_ready), initializing stream connection...")
        # Enable auto-reconnect loop and start
        self._stream_should_run = True
        print("[MOUNT] Stream enabled, calling auto_connect_stream()")
        self.auto_connect_stream()
    
    def _ensure_stream_started(self):
        """Idempotently start the stream if not already started"""
        print("[ENSURE] _ensure_stream_started called")
        if getattr(self, "_auto_started", False):
            print("[ENSURE] Stream already started, skipping")
            return
        print("[ENSURE] Starting stream for first time...")
        self._auto_started = True
        self._stream_should_run = True
        try:
            asyncio.create_task(self.connect_to_stream())
            print("[ENSURE] Stream connect task created successfully")
        except Exception as e:
            print(f"[ENSURE] Failed to create stream connect task: {e}")
    
    async def connect_to_stream(self):
        """Connect to the streaming API endpoint using EventSource (SSE) if possible."""
        try:
            if hasattr(self, "_stream_should_run") and not self._stream_should_run:
                print("[SSE] Stream connection cancelled - _stream_should_run is False")
                return
            # Avoid duplicate EventSource instances
            if getattr(self, "_event_source", None) is not None:
                print("[SSE] EventSource already exists, skipping duplicate connection")
                return

            print("[SSE] Starting stream connection...")
            # Update state using proper mutation to trigger reactivity
            with self.state.mutate("connection_status"):
                self.state["connection_status"] = "Connected - waiting for data"
            with self.state.mutate("is_connected"):
                self.state["is_connected"] = True

            url = "https://trailbase.nandi.crabdance.com/api/records/v1/people/subscribe/*"
            print(f"[SSE] Attempting to connect to: {url}")
            
            try:
                print("[SSE] Creating new EventSource...")
                es = window.EventSource.new(url)
                self._event_source = es
                print("[SSE] EventSource created successfully")

                def on_open(e):
                    print("[SSE] Connection opened successfully")
                    print(f"[SSE] Event object: {e}")
                    # Update state using proper mutation
                    with self.state.mutate("connection_status"):
                        self.state["connection_status"] = "Connected - waiting for data"
                    with self.state.mutate("is_connected"):
                        self.state["is_connected"] = True

                async def process_payload_text(payload_text: str):
                    print(f"[SSE] Processing payload: {payload_text[:200]}{'...' if len(payload_text) > 200 else ''}")
                    try:
                        data_obj = json.loads(payload_text)
                        print(f"[SSE] Successfully parsed JSON with {len(data_obj) if isinstance(data_obj, (dict, list)) else 'unknown'} items")
                        # Only add JSON data to UI
                        data_obj["timestamp"] = int(time.time() * 1000)  # Convert to milliseconds like Date.now()
                        new_list = list(self.state.get("stream_data", [])) + [data_obj]
                        if len(new_list) > 50:
                            new_list = new_list[-50:]
                        self.state["stream_data"] = new_list
                        print(f"[SSE] Added JSON to stream data, total records: {len(new_list)}")
                    except Exception as e:
                        # Try to determine the type of non-JSON data
                        data_type = "unknown"
                        if not payload_text or payload_text.strip() == "":
                            data_type = "empty/whitespace"
                        elif payload_text.startswith("data:"):
                            data_type = "SSE data line"
                        elif payload_text.startswith("event:"):
                            data_type = "SSE event line"
                        elif payload_text.startswith("id:"):
                            data_type = "SSE id line"
                        elif payload_text.startswith("retry:"):
                            data_type = "SSE retry line"
                        elif payload_text.strip() == ":":
                            data_type = "SSE comment/heartbeat"
                        elif payload_text.startswith(":"):
                            data_type = "SSE comment"
                        elif payload_text.lower().startswith("<!doctype") or payload_text.lower().startswith("<html"):
                            data_type = "HTML page"
                        elif payload_text.startswith("<"):
                            data_type = "XML/HTML fragment"
                        elif "error" in payload_text.lower():
                            data_type = "error message"
                        elif "connect" in payload_text.lower():
                            data_type = "connection message"
                        elif payload_text.isdigit():
                            data_type = "numeric string"
                        else:
                            data_type = "plain text"
                        
                        print(f"[SSE] Non-JSON payload [{data_type}] (not adding to UI): {payload_text}")
                        print(f"[SSE] JSON parse error: {e}")

                def on_message(e):
                    print("[SSE] Message received from server")
                    try:
                        payload = e.data
                        print(f"[SSE] Raw payload type: {type(payload)}")
                        try:
                            payload_text = payload.to_py() if hasattr(payload, "to_py") else payload
                        except Exception as convert_ex:
                            print(f"[SSE] Failed to convert payload: {convert_ex}")
                            payload_text = payload
                        if not isinstance(payload_text, str):
                            payload_text = str(payload_text)
                        print(f"[SSE] Converted payload length: {len(payload_text)} chars")
                        # Schedule async processing to avoid blocking
                        asyncio.create_task(process_payload_text(payload_text))
                    except Exception as ex:
                        print(f"[SSE] Error processing message: {ex}")

                def on_error(e):
                    print(f"[SSE] Connection error occurred: {e}")
                    print(f"[SSE] Error type: {type(e)}")
                    try:
                        print(f"[SSE] Error details: readyState={getattr(e.target, 'readyState', 'unknown')}")
                    except Exception:
                        pass
                    # Mark disconnected and cleanup using proper mutation
                    with self.state.mutate("is_connected"):
                        self.state["is_connected"] = False
                    with self.state.mutate("connection_status"):
                        self.state["connection_status"] = "Disconnected"
                    try:
                        if getattr(self, "_event_source", None) is not None:
                            print("[SSE] Closing EventSource...")
                            self._event_source.close()
                    except Exception as close_ex:
                        print(f"[SSE] Error closing EventSource: {close_ex}")
                    self._event_source = None
                    # Auto-reconnect if allowed
                    if getattr(self, "_stream_should_run", True):
                        print("[SSE] Scheduling reconnect in 2 seconds...")
                        with self.state.mutate("connection_status"):
                            self.state["connection_status"] = "Reconnecting in 2s..."
                        asyncio.create_task(self._reconnect_after_delay())
                    else:
                        print("[SSE] Auto-reconnect disabled")

                print("[SSE] Setting up event handlers...")
                es.onopen = on_open
                es.onmessage = on_message
                es.onerror = on_error
                print("[SSE] Event handlers configured")
                
                # Set a timeout to fallback to fetch if SSE doesn't work
                print("[SSE] Starting timeout fallback task...")
                asyncio.create_task(self._sse_timeout_fallback())
                
            except Exception as sse_error:
                print(f"[SSE] EventSource creation failed: {sse_error}")
                self.state["is_connected"] = False
                with self.state.mutate("connection_status"):
                    self.state["connection_status"] = f"SSE Error: {str(sse_error)}"
                
        except Exception as e:
            print(f"[SSE] Overall connection error: {e}")
            self.state["is_connected"] = False
            with self.state.mutate("connection_status"):
                self.state["connection_status"] = f"Error: {str(e)}"
    
    async def _sse_timeout_fallback(self):
        """Timeout to check for heartbeat/data after 1 minute"""
        try:
            print("[SSE] Starting 60-second timeout for heartbeat check...")
            await asyncio.sleep(60)
            if not self.state.get("is_connected", False):
                print("[SSE] No heartbeat/data received within 60 seconds")
                with self.state.mutate("connection_status"):
                    self.state["connection_status"] = "No heartbeat - connection may be dead"
                self.state["is_connected"] = False
            else:
                print("[SSE] Heartbeat timeout passed - connection appears active")
        except Exception as e:
            print(f"[SSE] Heartbeat timeout check error: {e}")
    
    async def _connect_with_fetch_REMOVED(self):
        """Fallback connection using fetch API"""
        try:
            print("[FETCH] Starting fetch-based streaming connection...")
            self.state["connection_status"] = "Connecting (fetch)..."
            
            # Prepare AbortController for clean disconnects
            print("[FETCH] Creating AbortController...")
            controller = window.AbortController.new()
            self._stream_controller = controller

            # Build fetch options as native JS object
            fetch_opts = window.Object.new()
            fetch_opts.signal = controller.signal
            print("[FETCH] Fetch options configured with abort signal")

            url = "https://trailbase.nandi.crabdance.com/api/records/v1/people/subscribe/*"
            print(f"[FETCH] Attempting fetch request to: {url}")
            # Use fetch API to connect to the stream with abort signal
            response = await window.fetch(url, fetch_opts)
            print(f"[FETCH] Response received - status: {response.status}, ok: {response.ok}")

            if response.ok:
                print("[FETCH] Response OK, starting stream reading...")
                self.state["connection_status"] = "Connected (fetch)"
                self.state["is_connected"] = True

                # Get the readable stream and a UTF-8 decoder
                print("[FETCH] Getting response body reader...")
                reader = response.body.getReader()
                decoder = window.TextDecoder.new("utf-8")
                print("[FETCH] TextDecoder initialized")

                # Buffers for handling partial lines and SSE events
                text_buffer = ""
                sse_data_lines = []

                async def handle_parsed_payload(payload_text: str):
                    print(f"[FETCH] Processing payload: {payload_text[:200]}{'...' if len(payload_text) > 200 else ''}")
                    # Try to parse NDJSON/SSE data string into JSON
                    try:
                        data_obj = json.loads(payload_text)
                        print(f"[FETCH] Successfully parsed JSON with {len(data_obj) if isinstance(data_obj, (dict, list)) else 'unknown'} items")
                        # Only add JSON data to UI
                        data_obj["timestamp"] = int(time.time() * 1000)  # Convert to milliseconds like Date.now()
                        new_list = list(self.state.get("stream_data", [])) + [data_obj]
                        # Keep only last 50
                        if len(new_list) > 50:
                            new_list = new_list[-50:]
                        self.state["stream_data"] = new_list
                        print(f"[FETCH] Added JSON to stream data, total records: {len(new_list)}")
                    except Exception as e:
                        # Try to determine the type of non-JSON data
                        data_type = "unknown"
                        if not payload_text or payload_text.strip() == "":
                            data_type = "empty/whitespace"
                        elif payload_text.startswith("data:"):
                            data_type = "SSE data line"
                        elif payload_text.startswith("event:"):
                            data_type = "SSE event line"
                        elif payload_text.startswith("id:"):
                            data_type = "SSE id line"
                        elif payload_text.startswith("retry:"):
                            data_type = "SSE retry line"
                        elif payload_text.strip() == ":":
                            data_type = "SSE comment/heartbeat"
                        elif payload_text.startswith(":"):
                            data_type = "SSE comment"
                        elif payload_text.lower().startswith("<!doctype") or payload_text.lower().startswith("<html"):
                            data_type = "HTML page"
                        elif payload_text.startswith("<"):
                            data_type = "XML/HTML fragment"
                        elif "error" in payload_text.lower():
                            data_type = "error message"
                        elif "connect" in payload_text.lower():
                            data_type = "connection message"
                        elif payload_text.isdigit():
                            data_type = "numeric string"
                        else:
                            data_type = "plain text"
                        
                        print(f"[FETCH] Non-JSON payload [{data_type}] (not adding to UI): {payload_text}")
                        print(f"[FETCH] JSON parse error: {e}")

                # Start reading the stream
                print("[FETCH] Starting stream reading loop...")
                while True:
                    try:
                        result = await reader.read()
                        if result.done:
                            print("[FETCH] Stream reading completed (done=True)")
                            break

                        # Decode the Uint8Array chunk using TextDecoder
                        chunk_text = decoder.decode(result.value)
                        if not isinstance(chunk_text, str):
                            chunk_text = str(chunk_text)
                        
                        print(f"[FETCH] Received chunk: {len(chunk_text)} chars")
                        text_buffer += chunk_text

                        # Process complete lines; keep trailing partial in buffer
                        while "\n" in text_buffer:
                            line, text_buffer = text_buffer.split("\n", 1)
                            line = line.rstrip("\r")

                            # Handle SSE format: accumulate data: lines until blank line
                            if line == "":
                                if sse_data_lines:
                                    payload = "\n".join(sse_data_lines)
                                    print(f"[FETCH] Processing SSE event with {len(sse_data_lines)} data lines")
                                    sse_data_lines = []
                                    await handle_parsed_payload(payload)
                                continue

                            if line.startswith("data:"):
                                data_content = line[5:].lstrip()
                                print(f"[FETCH] SSE data line: {data_content[:100]}{'...' if len(data_content) > 100 else ''}")
                                sse_data_lines.append(data_content)
                                continue

                            # Handle NDJSON/plain lines
                            stripped = line.strip()
                            if stripped:
                                print(f"[FETCH] Processing NDJSON line: {stripped[:100]}{'...' if len(stripped) > 100 else ''}")
                                await handle_parsed_payload(stripped)

                    except Exception as e:
                        print(f"[FETCH] Error during stream reading: {e}")
                        # If aborted, exit quietly
                        try:
                            if getattr(self, "_stream_controller", None) and self._stream_controller.signal.aborted:
                                print("[FETCH] Stream reading aborted by signal")
                                break
                        except Exception as abort_check_ex:
                            print(f"[FETCH] Error checking abort signal: {abort_check_ex}")
                        print("[FETCH] Breaking from stream reading loop due to error")
                        break

                # Flush remaining SSE data on stream end
                if sse_data_lines:
                    payload = "\n".join(sse_data_lines)
                    print(f"[FETCH] Flushing remaining {len(sse_data_lines)} SSE data lines on stream end")
                    sse_data_lines = []
                    await handle_parsed_payload(payload)

            else:
                print(f"[FETCH] Response not OK - status: {response.status}")
                self.state["connection_status"] = f"Connection failed: {response.status}"
                # SSE-only mode - no fallbacks
                print("[FETCH] SSE-only mode - no polling fallback")
                self.state["connection_status"] = "SSE connection failed - no fallbacks"

        except Exception as e:
            print(f"[FETCH] Connection error: {e}")
            # If aborted before response
            try:
                if getattr(self, "_stream_controller", None) and self._stream_controller.signal.aborted:
                    print("[FETCH] Connection was aborted")
                    self.state["connection_status"] = "Disconnected"
                else:
                    print(f"[FETCH] Connection failed with error: {e}")
                    self.state["connection_status"] = f"Error: {str(e)}"
            except Exception as status_ex:
                print(f"[FETCH] Error setting connection status: {status_ex}")
                self.state["connection_status"] = f"Error: {str(e)}"
            # SSE-only mode - no fallbacks
            print("[FETCH] SSE-only mode - no polling fallback")
            self.state["connection_status"] = "SSE connection failed - no fallbacks"
        finally:
            print("[FETCH] Cleaning up fetch connection...")
            self.state["is_connected"] = False
            # Auto-reconnect unless user explicitly disconnected
            try:
                aborted = False
                if getattr(self, "_stream_controller", None):
                    aborted = bool(self._stream_controller.signal.aborted)
                print(f"[FETCH] Connection aborted: {aborted}")
            except Exception as abort_check_ex:
                print(f"[FETCH] Error checking abort status: {abort_check_ex}")
                aborted = False
            if getattr(self, "_stream_should_run", True) and not aborted:
                print("[FETCH] Scheduling reconnect in 2 seconds...")
                self.state["connection_status"] = "Reconnecting in 2s..."
                asyncio.create_task(self._reconnect_after_delay())
            else:
                print("[FETCH] Auto-reconnect disabled or connection was aborted")
    
    async def _connect_with_polling_REMOVED(self):
        """Final fallback: simple polling approach"""
        try:
            print("[POLLING] Starting polling connection...")
            self.state["connection_status"] = "Connected (polling)"
            self.state["is_connected"] = True
            
            # Store last update time to detect changes
            self._last_poll_time = 0
            print("[POLLING] Initialized polling state")
            
            poll_count = 0
            while getattr(self, "_stream_should_run", True):
                poll_count += 1
                try:
                    # Poll the people endpoint to check for updates
                    url = "https://trailbase.nandi.crabdance.com/api/records/v1/people"
                    print(f"[POLLING] Poll #{poll_count}: requesting {url}")
                    response = await window.fetch(url)
                    
                    if response.ok:
                        print(f"[POLLING] Poll #{poll_count} successful - status: {response.status}")
                        data = await response.json()
                        print(f"[POLLING] Poll #{poll_count} received data: {len(data) if isinstance(data, (list, dict)) else 'unknown'} items")
                        current_time = int(time.time() * 1000)  # Convert to milliseconds like Date.now()
                        
                        # Create a simple update event
                        update_event = {
                            "type": "poll_update",
                            "timestamp": current_time,
                            "data": data,
                            "poll_time": current_time,
                            "poll_number": poll_count
                        }
                        
                        # Add to stream data
                        new_list = list(self.state.get("stream_data", [])) + [update_event]
                        if len(new_list) > 50:
                            new_list = new_list[-50:]
                        self.state["stream_data"] = new_list
                        print(f"[POLLING] Poll #{poll_count} added to stream data, total records: {len(new_list)}")
                        
                    else:
                        print(f"[POLLING] Poll #{poll_count} failed - status: {response.status}")
                        
                except Exception as e:
                    print(f"[POLLING] Poll #{poll_count} error: {e}")
                
                # Wait 3 seconds before next poll
                print(f"[POLLING] Poll #{poll_count} complete, waiting 3 seconds...")
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"[POLLING] Overall polling error: {e}")
            self.state["is_connected"] = False
            self.state["connection_status"] = f"Polling error: {str(e)}"

    async def _reconnect_after_delay(self):
        print("[RECONNECT] Starting 2-second delay before reconnect...")
        try:
            await asyncio.sleep(2)
        except Exception as sleep_ex:
            print(f"[RECONNECT] Sleep interrupted: {sleep_ex}")
            return
        if getattr(self, "_stream_should_run", True) and not self.state.get("is_connected", False):
            print("[RECONNECT] Attempting to reconnect...")
            try:
                asyncio.create_task(self.connect_to_stream())
                print("[RECONNECT] Reconnect task created successfully")
            except Exception as e:
                print(f"[RECONNECT] Failed to create reconnect task: {e}")
        else:
            print(f"[RECONNECT] Skipping reconnect - should_run: {getattr(self, '_stream_should_run', True)}, is_connected: {self.state.get('is_connected', False)}")
    
    def handle_connect_stream(self, event):
        """Handle connect button click"""
        # Use a more compatible approach for browser environment
        try:
            asyncio.create_task(self.connect_to_stream())
        except Exception as e:
            pass
            self.state["connection_status"] = f"Failed to start: {str(e)}"
    
    def handle_disconnect_stream(self, event):
        """Handle disconnect button click"""
        try:
            if hasattr(event, "preventDefault"):
                event.preventDefault()
            if hasattr(event, "stopPropagation"):
                event.stopPropagation()
        except Exception:
            pass
        # no logs
        # Disable auto-reconnect loop and close SSE
        try:
            if getattr(self, "_event_source", None) is not None:
                self._event_source.close()
                pass
        except Exception as e:
            pass
        self._event_source = None
        # Disable auto-reconnect loop
        self._stream_should_run = False
        self.state["is_connected"] = False
        with self.state.mutate("connection_status"):
            self.state["connection_status"] = "Disconnected"
        pass
    
    def handle_clear_stream_data(self, event):
        """Clear the stream data"""
        try:
            if hasattr(event, "preventDefault"):
                event.preventDefault()
            if hasattr(event, "stopPropagation"):
                event.stopPropagation()
        except Exception:
            pass
        
        print("[CLEAR] Clearing stream data...")
        current_count = len(self.state.get("stream_data", []))
        self.state["stream_data"] = []
        print(f"[CLEAR] Cleared {current_count} stream data records")
    
    def handle_update_user_2_click(self, event):
        """Schedule async update of user 2"""
        try:
            if hasattr(event, "preventDefault"):
                event.preventDefault()
            if hasattr(event, "stopPropagation"):
                event.stopPropagation()
        except Exception:
            pass
        # no logs
        try:
            asyncio.create_task(self.update_user_2(event))
        except Exception as e:
            pass

    async def update_user_2(self, event):
        """Update user ID 2 with random data"""
        try:
            import random
            
            pass
            
            # Generate random name and age
            names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
            random_name = random.choice(names)
            random_age = random.randint(18, 80)
            
            pass
            
            # Create the user data as a JavaScript object
            user_data = window.Object.new()
            user_data.name = random_name
            user_data.age = random_age
            
            # Create fetch options as JavaScript object
            fetch_options = window.Object.new()
            fetch_options.method = "PATCH"
            fetch_options.headers = window.Object.new()
            fetch_options.headers["Content-Type"] = "application/json"
            fetch_options.body = window.JSON.stringify(user_data)
            
            pass
            
            # Send PATCH request to update user ID 2
            response = await window.fetch(
                "https://trailbase.nandi.crabdance.com/api/records/v1/people/2",
                fetch_options
            )
            
            if response.ok:
                print(f"[UPDATE] Successfully updated user 2 with name: {random_name}, age: {random_age}")
                print("[UPDATE] Change should appear automatically via stream subscription")
            else:
                print(f"[UPDATE] Failed to update user 2 - status: {response.status}")
                try:
                    error_text = await response.text()
                    print(f"[UPDATE] Error details: {error_text}")
                except Exception:
                    pass
                
        except Exception as e:
            pass
    
    async def _force_polling_update_REMOVED(self):
        """Force an immediate polling update to see the change"""
        try:
            print("[FORCE_POLL] Forcing immediate polling update")
            response = await window.fetch("https://trailbase.nandi.crabdance.com/api/records/v1/people")
            
            if response.ok:
                data = await response.json()
                
                # Log the forced update but don't add to UI
                print(f"[FORCE_POLL] Forced polling update received {len(data) if isinstance(data, (list, dict)) else 'unknown'} records")
                print(f"[FORCE_POLL] Data preview: {str(data)[:200]}{'...' if len(str(data)) > 200 else ''}")
                
        except Exception as e:
            print(f"[FORCE_POLL] Forced polling error: {e}")
    
    def auto_connect_stream(self):
        """Auto-connect to stream on page load"""
        print("[AUTO] Auto-connect stream called")
        # Defer a bit to avoid race with mount/render/event loop init
        def _start_connect():
            print("[AUTO] Auto-connect timeout fired; starting stream")
            try:
                print("[AUTO] Creating asyncio task for connect_to_stream...")
                task = asyncio.create_task(self.connect_to_stream())
                print(f"[AUTO] Connect task created successfully: {task}")
            except Exception as e:
                print(f"[AUTO] Failed to auto-connect stream: {e}")
                with self.state.mutate("connection_status"):
                    self.state["connection_status"] = f"Auto-connect failed: {str(e)}"
        
        # Try setTimeout first, but also start immediately as backup
        try:
            print("[AUTO] Attempting to use setTimeout...")
            window.setTimeout(_start_connect, 250)
            print("[AUTO] Auto-connect scheduled for 250ms delay")
        except Exception as e:
            print(f"[AUTO] setTimeout not available or failed: {e}")
        
        # Also start immediately to ensure connection attempt
        print("[AUTO] Starting connection immediately as well...")
        _start_connect()
    
    def handle_increment(self, event):
        self.state["count"] += 1
        self.persist_state()

    def handle_decrement(self, event):
        self.state["count"] -= 1
        self.persist_state()

    def handle_reset_count(self, event):
        self.state["count"] = 0
        self.persist_state()
    
    def handle_input_change(self, event):
        self.state["input_text"] = event.target.value
    
    def handle_input_keydown(self, event):
        if event.key == "Enter":
            self.handle_add_todo(event)
    
    def handle_add_todo(self, event):
        todo_text = self.state["input_text"].strip()
        if todo_text:
            current_todos = self.state["todos"]
            self.state["todos"] = current_todos + [todo_text]
            self.state["input_text"] = ""
            pass
            self.persist_state()
        else:
            pass
    
    def handle_remove_todo(self, event, index):
        pass
        try:
            if 0 <= index < len(self.state["todos"]):
                current_todos = self.state["todos"]
                self.state["todos"] = current_todos[:index] + current_todos[index+1:]
                pass
                self.persist_state()
            else:
                pass
        except Exception as e:
            pass

    def handle_remove_completed(self, event, index):
        pass
        try:
            if 0 <= index < len(self.state["completed"]):
                current_completed = self.state["completed"]
                self.state["completed"] = current_completed[:index] + current_completed[index+1:]
                pass
                self.persist_state()
            else:
                pass
        except Exception as e:
            pass

    def handle_complete_todo(self, event, index):
        pass
        try:
            if 0 <= index < len(self.state["todos"]):
                todo = self.state["todos"][index]
                # Move to completed creating new lists for reactivity
                new_todos = self.state["todos"][:index] + self.state["todos"][index+1:]
                new_completed = self.state["completed"] + [todo]
                self.state["todos"] = new_todos
                self.state["completed"] = new_completed
                pass
                self.persist_state()
                # Trigger confetti if available
                try:
                    if hasattr(window, "__confetti__"):
                        # Burst confetti from center
                        window.__confetti__.call(None, {"particleCount": 120, "spread": 70, "origin": {"y": 0.6}})
                except Exception as e2:
                    pass
        except Exception as e:
            pass

    def handle_uncomplete_todo(self, event, index):
        pass
        try:
            if 0 <= index < len(self.state["completed"]):
                todo = self.state["completed"][index]
                new_completed = self.state["completed"][:index] + self.state["completed"][index+1:]
                new_todos = self.state["todos"] + [todo]
                self.state["completed"] = new_completed
                self.state["todos"] = new_todos
                pass
                self.persist_state()
        except Exception as e:
            pass

    def goto_test(self, event):
        """Navigate to the test route using client-side routing"""
        if self.router:
            # Use the router's reverse method to generate the correct URL with base path
            test_url = self.router.reverse("test")
            self.router.navigate_to_path(test_url)
        else:
            # Fallback to direct navigation if router is not available
            from js import window
            window.location = f"{base_path}/test"

    def persist_state(self):
        try:
            state_snapshot = {
                "count": self.state.get("count", 0),
                "input_text": self.state.get("input_text", ""),
                "todos": list(self.state.get("todos", [])),
                "completed": list(self.state.get("completed", [])),
            }
            if hasattr(window, "__opfs__"):
                import json
                # Pass JSON string to avoid proxy conversion issues
                window.__opfs__.saveState(json.dumps(state_snapshot))
        except Exception as e:
            pass
    
    def populate(self):
        t.h1("Hello, World!", class_name="text-3xl font-bold mb-6 text-center text-catppuccin-mauve")
        
        # Counter section
        with t.div(class_name="card"):
            t.h2("Counter", class_name="text-xl font-semibold mb-3 text-catppuccin-blue")
            t.p(f"Count: {self.state['count']}", class_name="mb-3 text-catppuccin-green")
            with t.div(class_name="flex gap-2"):
                t.button(
                    "Decrement",
                    on_click=self.handle_decrement,
                    class_name="btn-base btn-red"
                )
                t.button(
                    "Reset",
                    on_click=self.handle_reset_count,
                    class_name="btn-base btn-mauve"
                )
                t.button(
                    "Increment",
                    on_click=self.handle_increment,
                    class_name="btn-base btn-blue"
                )
        
        # Todo input section
        with t.div(class_name="card"):
            t.h2("Add Todo", class_name="text-xl font-semibold mb-3 text-catppuccin-blue")
            # Using flexbox for responsive layout with proper spacing on mobile
            with t.div(class_name="flex flex-col sm:flex-row sm:items-center gap-2"):
                t.input(
                    placeholder="What needs to be done?",
                    value=self.state["input_text"],
                    on_input=self.handle_input_change,
                    on_keydown=self.handle_input_keydown,
                    class_name="input-base"
                )
                t.button("Add Todo", on_click=self.handle_add_todo, class_name="btn-base btn-green whitespace-nowrap")
        
        # Active todos section
        with t.div(class_name="card"):
            t.h2("To Do", class_name="text-xl font-semibold mb-3 text-catppuccin-blue")
            if len(self.state["todos"]) == 0:
                t.p("Nothing to do. Add a task above.", class_name="text-catppuccin-subtext0")
            else:
                with t.ul(class_name="list-none p-0"):
                    for index, todo in enumerate(self.state["todos"]):
                        with t.li(class_name="flex justify-between items-center py-2 border-b border-catppuccin-surface1"):
                            t.span(todo, class_name="text-catppuccin-text")
                            with t.div(class_name="flex gap-2"):
                                t.button(
                                    "Complete",
                                    on_click=lambda e, idx=index: self.handle_complete_todo(e, idx),
                                    class_name="btn-sm btn-green"
                                )
                                t.button(
                                    "Remove",
                                    on_click=lambda e, idx=index: self.handle_remove_todo(e, idx),
                                    class_name="btn-sm btn-red"
                                )

        # Completed todos section
        with t.div(class_name="card"):
            t.h2("Completed", class_name="text-xl font-semibold mb-3 text-catppuccin-blue")
            if len(self.state["completed"]) == 0:
                t.p("No completed tasks yet.", class_name="text-catppuccin-subtext0")
            else:
                with t.ul(class_name="list-none p-0"):
                    for index, todo in enumerate(self.state["completed"]):
                        with t.li(class_name="flex justify-between items-center py-2 border-b border-catppuccin-surface1"):
                            t.span(todo, class_name="line-through text-catppuccin-text")
                            with t.div(class_name="flex gap-2"):
                                t.button(
                                    "Undo",
                                    on_click=lambda e, idx=index: self.handle_uncomplete_todo(e, idx),
                                    class_name="btn-sm btn-green"
                                )
                                t.button(
                                    "Remove",
                                    on_click=lambda e, idx=index: self.handle_remove_completed(e, idx),
                                    class_name="btn-sm btn-red"
                                )

        # Streaming API section
        with t.div(class_name="card"):
            t.h2("Live Stream Data", class_name="text-xl font-semibold mb-3 text-catppuccin-blue")
            
            # Navigation links
            with t.div(class_name="mb-4"):
                t.button("Go to Test Route", on_click=self.goto_test, class_name="btn-base btn-green mr-2")
            
            # Connection status and controls
            with t.div(class_name="mb-4"):
                # Debug: Let's see what's really happening
                status_text = f"Status: {self.state['connection_status']}"
                is_connected = "Connected" in self.state["connection_status"]
                
                import time
                print(f"DEBUG RENDER: populate() called at {time.time()}")
                print(f"DEBUG RENDER: connection_status = '{self.state['connection_status']}'")
                print(f"DEBUG RENDER: is_connected = {is_connected}")
                
                if is_connected:
                    print(f"DEBUG RENDER: Using GREEN inline style")
                    t.p(status_text, 
                        style="margin-bottom: 0.5rem; color: #a6e3a1;", 
                        key="status-green")
                else:
                    print(f"DEBUG RENDER: Using RED inline style") 
                    t.p(status_text, 
                        style="margin-bottom: 0.5rem; color: #f38ba8;", 
                        key="status-red")
                
                with t.div(class_name="flex gap-2 flex-wrap"):
                    # Update User 2 button
                    t.button(
                        "Update User 2 (Random Data)",
                        on_click=self.handle_update_user_2_click,
                        class_name="btn-base btn-blue",
                        key="btn-update-user"
                    )
                    
                    # Clear data button
                    if len(self.state["stream_data"]) > 0:
                        t.button(
                            "Clear Data",
                            on_click=self.handle_clear_stream_data,
                            class_name="btn-base btn-mauve",
                            key="btn-clear-data"
                        )
            
            # Stream data display
            if len(self.state["stream_data"]) == 0:
                t.p("No stream data received yet. Stream auto-connects on page load. Click 'Update User 2' to generate test data.", 
                    class_name="text-catppuccin-subtext0")
            else:
                t.p(f"Received {len(self.state['stream_data'])} records:", 
                    class_name="mb-3 text-catppuccin-text")
                
                # Display the most recent data first
                for i, data in enumerate(reversed(self.state["stream_data"])):
                    record_number = len(self.state['stream_data']) - i
                    # Create unique key for each record to prevent rendering issues
                    record_key = f"record-{record_number}-{data.get('timestamp', i)}"
                    with t.div(class_name="mb-3 p-3 rounded border bg-catppuccin-surface1 border-catppuccin-surface2", key=record_key):
                        t.p(f"Record #{record_number}",
                            class_name="font-semibold mb-2 text-catppuccin-blue")
                        
                        # Display timestamp if available
                        if "timestamp" in data:
                            try:
                                # Handle both string timestamps and numeric timestamps
                                if isinstance(data["timestamp"], str):
                                    # If it's a string, try to parse it as a number
                                    timestamp_num = float(data["timestamp"])
                                else:
                                    timestamp_num = data["timestamp"]
                                
                                timestamp = window.Date(timestamp_num).toLocaleString()
                                t.p(f"Time: {timestamp}", 
                                    class_name="text-sm mb-2 text-catppuccin-subtext0")
                            except Exception as e:
                                # Fallback to showing the raw timestamp
                                t.p(f"Time: {data['timestamp']}", 
                                    class_name="text-sm mb-2 text-catppuccin-subtext0")
                        
                        # Display the data as formatted JSON with proper width constraints
                        try:
                            formatted_json = json.dumps(data, indent=2)
                            t.pre(formatted_json, 
                                  class_name="json-display")
                        except Exception:
                            t.p(str(data), 
                                class_name="text-sm break-words text-catppuccin-text")


# Define routes without base path in the decorator
@app.page("/test", name="test")
class TestPage(Page):
    def goto_home(self, event):
        """Navigate to the home route using client-side routing"""
        if self.router:
            # Navigate to the default page
            self.router.navigate_to_path("/")
        else:
            # Fallback to direct navigation if router is not available
            from js import window
            window.location = f"{base_path}/"
    
    def populate(self):
        t.h1("Test Route Page", class_name="text-3xl font-bold mb-6 text-center text-catppuccin-mauve")
        t.p("This is a test route page created with PuePy routing!", class_name="mb-4")
        t.button("Go back to Home", on_click=self.goto_home, class_name="btn-base btn-blue")


print("[STARTUP] Mounting app to #app...")
# Check for redirect path from 404.html redirect (for GitHub Pages)
redirect_path = None
try:
    from js import sessionStorage
    redirect_path = sessionStorage.getItem('redirectPath')
    if redirect_path:
        sessionStorage.removeItem('redirectPath')
        # Remove the base path from the redirect path if present
        if base_path and redirect_path.startswith(base_path):
            redirect_path = redirect_path[len(base_path):]
            if not redirect_path:
                redirect_path = "/"
except:
    pass

# Mount the app with the redirect path if available
try:
    if redirect_path:
        app.mount("#app", path=redirect_path)
    else:
        app.mount("#app")
    print("[STARTUP] App mounted successfully")
except Exception as e:
    print(f"[STARTUP] Failed to mount app: {e}")

# Force auto-connect since on_mount might not be called
print("[STARTUP] Manually triggering auto-connect...")
try:
    # Get the page instance and call auto_connect
    if hasattr(app, 'page_instance'):
        app.page_instance.auto_connect_stream()
except Exception as e:
    print(f"[STARTUP] Failed to manually trigger auto-connect: {e}")
    # Try a different approach - create a delayed task
    try:
        def delayed_connect():
            print("[STARTUP] Delayed connect attempting...")
            # This will run after the page is fully initialized
            import asyncio
            from js import document
            app_element = document.getElementById("app")
            if app_element and hasattr(window, 'app_page_instance'):
                window.app_page_instance.auto_connect_stream()
        
        window.setTimeout(delayed_connect, 1000)
        print("[STARTUP] Scheduled delayed auto-connect")
    except Exception as e2:
        print(f"[STARTUP] Failed to schedule delayed auto-connect: {e2}")