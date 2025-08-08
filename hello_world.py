from puepy import Application, Page, t
import pyscript
import logging
from js import window

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Application()


@app.page()
class HelloWorldPage(Page):
    def initial(self):
        # Try to hydrate from OPFS-provided initial state
        try:
            import json
            raw = window.__INITIAL_STATE__
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
                            "completed": []
                        }
                        defaults.update({k: v for k, v in data.items() if k in defaults})
                        return defaults
        except Exception:
            pass
        return {
            "count": 0,
            "input_text": "",
            "todos": [],
            "completed": []
        }
    
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
            print(f"Todo '{todo_text}' added successfully. New todos: {self.state['todos']}")
            self.persist_state()
        else:
            print("Attempted to add empty todo")
    
    def handle_remove_todo(self, event, index):
        print(f"Attempting to remove todo at index: {index}")
        print(f"Current todos: {self.state['todos']}")
        try:
            if 0 <= index < len(self.state["todos"]):
                current_todos = self.state["todos"]
                self.state["todos"] = current_todos[:index] + current_todos[index+1:]
                print(f"Todo at index {index} removed successfully. New todos: {self.state['todos']}")
                self.persist_state()
            else:
                print(f"Index {index} out of range. Current todos: {self.state['todos']}")
        except Exception as e:
            logger.error(f"Error removing todo at index {index}: {str(e)}")

    def handle_remove_completed(self, event, index):
        print(f"Attempting to remove completed todo at index: {index}")
        print(f"Current completed: {self.state['completed']}")
        try:
            if 0 <= index < len(self.state["completed"]):
                current_completed = self.state["completed"]
                self.state["completed"] = current_completed[:index] + current_completed[index+1:]
                print(f"Completed todo at index {index} removed successfully. New completed: {self.state['completed']}")
                self.persist_state()
            else:
                print(f"Index {index} out of range. Current completed: {self.state['completed']}")
        except Exception as e:
            logger.error(f"Error removing completed todo at index {index}: {str(e)}")

    def handle_complete_todo(self, event, index):
        print(f"Completing todo at index: {index}")
        try:
            if 0 <= index < len(self.state["todos"]):
                todo = self.state["todos"][index]
                # Move to completed creating new lists for reactivity
                new_todos = self.state["todos"][:index] + self.state["todos"][index+1:]
                new_completed = self.state["completed"] + [todo]
                self.state["todos"] = new_todos
                self.state["completed"] = new_completed
                print(f"Moved '{todo}' to completed.")
                self.persist_state()
                # Trigger confetti if available
                try:
                    if hasattr(window, "__confetti__"):
                        # Burst confetti from center
                        window.__confetti__.call(None, {"particleCount": 120, "spread": 70, "origin": {"y": 0.6}})
                except Exception as e2:
                    logger.debug(f"Confetti not available or failed: {e2}")
        except Exception as e:
            logger.error(f"Error completing todo at index {index}: {str(e)}")

    def handle_uncomplete_todo(self, event, index):
        print(f"Restoring completed todo at index: {index}")
        try:
            if 0 <= index < len(self.state["completed"]):
                todo = self.state["completed"][index]
                new_completed = self.state["completed"][:index] + self.state["completed"][index+1:]
                new_todos = self.state["todos"] + [todo]
                self.state["completed"] = new_completed
                self.state["todos"] = new_todos
                print(f"Restored '{todo}' to todos.")
                self.persist_state()
        except Exception as e:
            logger.error(f"Error restoring completed todo at index {index}: {str(e)}")

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
            logger.debug(f"persist_state failed: {e}")
    
    def populate(self):
        t.h1("Hello, World!", class_name="text-3xl font-bold mb-6 text-center", style="color: var(--catppuccin-mauve);")
        
        # Counter section
        with t.div(class_name="m-4 p-4 rounded-lg border", style="background-color: var(--catppuccin-surface0); border-color: var(--catppuccin-surface2);"):
            t.h2("Counter", class_name="text-xl font-semibold mb-3", style="color: var(--catppuccin-blue);")
            t.p(f"Count: {self.state['count']}", class_name="mb-3", style="color: var(--catppuccin-green);")
            with t.div(class_name="flex gap-2"):
                t.button(
                    "Decrement",
                    on_click=self.handle_decrement,
                    class_name="px-4 py-2 font-medium rounded-md transition-colors",
                    style="background-color: var(--catppuccin-red); color: var(--catppuccin-crust);"
                )
                t.button(
                    "Reset",
                    on_click=self.handle_reset_count,
                    class_name="px-4 py-2 font-medium rounded-md transition-colors",
                    style="background-color: var(--catppuccin-mauve); color: var(--catppuccin-crust);"
                )
                t.button(
                    "Increment",
                    on_click=self.handle_increment,
                    class_name="px-4 py-2 font-medium rounded-md transition-colors",
                    style="background-color: var(--catppuccin-blue); color: var(--catppuccin-crust);"
                )
        
        # Todo input section
        with t.div(class_name="m-4 p-4 rounded-lg border", style="background-color: var(--catppuccin-surface0); border-color: var(--catppuccin-surface2);"):
            t.h2("Add Todo", class_name="text-xl font-semibold mb-3", style="color: var(--catppuccin-blue);")
            # Using flexbox for responsive layout with proper spacing on mobile
            with t.div(class_name="flex flex-col sm:flex-row sm:items-center gap-2"):
                t.input(
                    placeholder="What needs to be done?",
                    value=self.state["input_text"],
                    on_input=self.handle_input_change,
                    on_keydown=self.handle_input_keydown,
                    class_name="flex-grow px-3 py-2 border rounded-md focus:outline-none focus:ring-2",
                    style="border-color: var(--catppuccin-overlay0); background-color: var(--catppuccin-surface1); color: var(--catppuccin-text);"
                )
                t.button("Add Todo", on_click=self.handle_add_todo, class_name="px-4 py-2 font-medium rounded-md transition-colors whitespace-nowrap", style="background-color: var(--catppuccin-green); color: var(--catppuccin-crust);")
        
        # Active todos section
        with t.div(class_name="m-4 p-4 rounded-lg border", style="background-color: var(--catppuccin-surface0); border-color: var(--catppuccin-surface2);"):
            t.h2("To Do", class_name="text-xl font-semibold mb-3", style="color: var(--catppuccin-blue);")
            if len(self.state["todos"]) == 0:
                t.p("Nothing to do. Add a task above.", style="color: var(--catppuccin-subtext0);")
            else:
                with t.ul(class_name="list-none p-0"):
                    for index, todo in enumerate(self.state["todos"]):
                        with t.li(class_name="flex justify-between items-center py-2 border-b", style="border-color: var(--catppuccin-surface1);"):
                            t.span(todo, style="color: var(--catppuccin-text);")
                            with t.div(class_name="flex gap-2"):
                                t.button(
                                    "Complete",
                                    on_click=lambda e, idx=index: self.handle_complete_todo(e, idx),
                                    class_name="px-3 py-1 font-medium rounded-md transition-colors",
                                    style="background-color: var(--catppuccin-green); color: var(--catppuccin-crust);"
                                )
                                t.button(
                                    "Remove",
                                    on_click=lambda e, idx=index: self.handle_remove_todo(e, idx),
                                    class_name="px-3 py-1 font-medium rounded-md transition-colors",
                                    style="background-color: var(--catppuccin-red); color: var(--catppuccin-crust);"
                                )

        # Completed todos section
        with t.div(class_name="m-4 p-4 rounded-lg border", style="background-color: var(--catppuccin-surface0); border-color: var(--catppuccin-surface2);"):
            t.h2("Completed", class_name="text-xl font-semibold mb-3", style="color: var(--catppuccin-blue);")
            if len(self.state["completed"]) == 0:
                t.p("No completed tasks yet.", style="color: var(--catppuccin-subtext0);")
            else:
                with t.ul(class_name="list-none p-0"):
                    for index, todo in enumerate(self.state["completed"]):
                        with t.li(class_name="flex justify-between items-center py-2 border-b", style="border-color: var(--catppuccin-surface1);"):
                            t.span(todo, class_name="line-through", style="color: var(--catppuccin-text);")
                            with t.div(class_name="flex gap-2"):
                                t.button(
                                    "Undo",
                                    on_click=lambda e, idx=index: self.handle_uncomplete_todo(e, idx),
                                    class_name="px-3 py-1 font-medium rounded-md transition-colors",
                                    style="background-color: var(--catppuccin-green); color: var(--catppuccin-crust);"
                                )
                                t.button(
                                    "Remove",
                                    on_click=lambda e, idx=index: self.handle_remove_completed(e, idx),
                                    class_name="px-3 py-1 font-medium rounded-md transition-colors",
                                    style="background-color: var(--catppuccin-red); color: var(--catppuccin-crust);"
                                )


app.mount("#app")