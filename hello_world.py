from puepy import Application, Page, t
import pyscript
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Application()


@app.page()
class HelloWorldPage(Page):
    def initial(self):
        return {
            "count": 0,
            "input_text": "",
            "items": ["Apple", "Banana", "Cherry"]
        }
    
    def handle_increment(self, event):
        self.state["count"] += 1
    
    def handle_input_change(self, event):
        self.state["input_text"] = event.target.value
    
    def handle_add_item(self, event):
        item_text = self.state["input_text"].strip()
        if item_text:
            self.state["items"].append(item_text)
            self.state["input_text"] = ""
            print(f"Item '{item_text}' added successfully. New list: {self.state['items']}")
        else:
            print("Attempted to add empty item")
    
    def handle_remove_item(self, event, index):
        print(f"Attempting to remove item at index: {index}")
        print(f"Current items list: {self.state['items']}")
        try:
            if 0 <= index < len(self.state["items"]):
                # Create a new list without the item at the specified index
                # This ensures reactivity by creating a new object reference
                current_items = self.state["items"]
                new_items = current_items[:index] + current_items[index+1:]
                self.state["items"] = new_items
                print(f"Item at index {index} removed successfully. New list: {self.state['items']}")
            else:
                print(f"Index {index} out of range. Current list: {self.state['items']}")
        except Exception as e:
            logger.error(f"Error removing item at index {index}: {str(e)}")
    
    def populate(self):
        t.h1("Hello, World!", class_name="text-3xl font-bold mb-6 text-center text-[#cba6f7]")
        
        # Counter section
        with t.div(class_name="m-4 p-4 rounded-lg bg-[#313244] border border-[#585b70]"):
            t.h2("Counter", class_name="text-xl font-semibold mb-3 text-[#89b4fa]")
            t.p(f"Count: {self.state['count']}", class_name="mb-3 text-[#a6e3a1]")
            t.button("Increment", on_click=self.handle_increment, class_name="px-4 py-2 bg-[#89b4fa] hover:bg-[#74c7ec] text-[#11111b] font-medium rounded-md transition-colors")
        
        # Text input section
        with t.div(class_name="m-4 p-4 rounded-lg bg-[#313244] border border-[#585b70]"):
            t.h2("Text Input", class_name="text-xl font-semibold mb-3 text-[#89b4fa]")
            # Using flexbox for responsive layout with proper spacing on mobile
            with t.div(class_name="flex flex-col sm:flex-row sm:items-center gap-2"):
                t.input(
                    placeholder="Enter some text...",
                    value=self.state["input_text"],
                    on_input=self.handle_input_change,
                    class_name="flex-grow px-3 py-2 border border-[#6c7086] rounded-md bg-[#45475a] text-[#cdd6f4] focus:outline-none focus:ring-2 focus:ring-[#89dceb]"
                )
                t.button("Add Item", on_click=self.handle_add_item, class_name="px-4 py-2 bg-[#a6e3a1] hover:bg-[#94e2d5] text-[#11111b] font-medium rounded-md transition-colors whitespace-nowrap")
        
        # List section
        with t.div(class_name="m-4 p-4 rounded-lg bg-[#313244] border border-[#585b70]"):
            t.h2("Item List", class_name="text-xl font-semibold mb-3 text-[#89b4fa]")
            with t.ul(class_name="list-none p-0"):
                for index, item in enumerate(self.state["items"]):
                    with t.li(class_name="flex justify-between items-center py-2 border-b border-[#45475a]"):
                        t.span(item, class_name="text-[#cdd6f4]")
                        # Use index-based removal to avoid closure issues
                        t.button(
                            "Remove",
                            on_click=lambda e, idx=index: self.handle_remove_item(e, idx),
                            class_name="px-3 py-1 bg-[#f38ba8] hover:bg-[#eba0ac] text-[#11111b] font-medium rounded-md transition-colors"
                        )


app.mount("#app")