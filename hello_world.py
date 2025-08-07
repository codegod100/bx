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
            logger.debug(f"Item '{item_text}' added successfully. New list: {self.state['items']}")
        else:
            logger.debug("Attempted to add empty item")
    
    def handle_remove_item(self, event, index):
        logger.debug(f"Attempting to remove item at index: {index}")
        logger.debug(f"Current items list: {self.state['items']}")
        try:
            if 0 <= index < len(self.state["items"]):
                # Create a new list without the item at the specified index
                # This ensures reactivity by creating a new object reference
                current_items = self.state["items"]
                new_items = current_items[:index] + current_items[index+1:]
                self.state["items"] = new_items
                logger.debug(f"Item at index {index} removed successfully. New list: {self.state['items']}")
            else:
                logger.debug(f"Index {index} out of range. Current list: {self.state['items']}")
        except Exception as e:
            logger.error(f"Error removing item at index {index}: {str(e)}")
    
    def populate(self):
        t.h1("Hello, World!")
        
        # Counter section
        with t.div(style="margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px;"):
            t.h2("Counter")
            t.p(f"Count: {self.state['count']}")
            t.button("Increment", on_click=self.handle_increment)
        
        # Text input section
        with t.div(style="margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px;"):
            t.h2("Text Input")
            t.input(
                placeholder="Enter some text...",
                value=self.state["input_text"],
                on_input=self.handle_input_change,
                style="padding: 8px; margin-right: 10px; border: 1px solid #999; border-radius: 3px;"
            )
            t.button("Add Item", on_click=self.handle_add_item)
            t.p(f"You entered: {self.state['input_text']}")
        
        # List section
        with t.div(style="margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px;"):
            t.h2("Item List")
            with t.ul():
                for index, item in enumerate(self.state["items"]):
                    with t.li():
                        t.span(item)
                        # Use index-based removal to avoid closure issues
                        t.button(
                            "Remove",
                            on_click=lambda e, idx=index: self.handle_remove_item(e, idx),
                            style="margin-left: 10px; padding: 3px 8px; background-color: #f44336; color: white; border: none; border-radius: 3px; cursor: pointer;"
                        )


app.mount("#app")