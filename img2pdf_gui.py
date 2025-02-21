import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pathlib
import time
import traceback
from img2pdf import img_to_pdf, draw_bounds_before_process
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pathlib
import time
import traceback
from img2pdf import img_to_pdf, draw_bounds_before_process
import threading
import queue
import json # Import the json module

class Img2PdfGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("img2pdf")

        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        default_margin = width // 100
        self.root.geometry(f"{width // 2}x{height // 2}+{default_margin}+{default_margin}")

        # Load translations
        self.translations = self.load_translations("translations.json") # Load from JSON file
        self.current_language = "sv" # Default language

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.process_frame = ttk.Frame(self.notebook)
        self.help_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.process_frame, text="Process") # Temporarily set default text
        self.notebook.add(self.help_frame, text="Help") # Temporarily set default text

        # --- Process Tab ---
        self.create_process_tab()

        # --- Help Tab ---
        self.create_help_tab()

        # Assign IDs to tabs *AFTER* creating tab content
        self.root.after(100, self.assign_tab_ids) # Delay ID assignment using root.after


        self.set_language(self.current_language) # Apply initial translation AFTER tabs and content are created!


        # Progress Bar (Initially hidden)
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=width // 2 - 20, mode="determinate")
        self.progress_bar.pack(pady=10)
        self.progress_bar["value"] = 0
        self.progress_label = tk.Label(root, text="0%")
        self.progress_label.pack()
        self.hide_progress()

        self.processing_queue = queue.Queue()
        self.files_processed = 0

    def assign_tab_ids(self):
        """Assigns id_str to notebook tabs after they are created."""
        try:
            children = self.notebook.winfo_children()
            if len(children) >= 2: # Ensure there are at least 2 children (tabs)
                children[0].id_str = "tab_process" # Assign ID to Process tab
                children[1].id_str = "tab_help" # Assign ID to Help tab
            else:
                self.root.after(100, self.assign_tab_ids) # Retry if not enough children yet
        except Exception as e:
            print(f"Error assigning tab IDs: {e}") # Log any errors during ID assignment



    def load_translations(self, filepath):
        """Loads translations from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f: # Specify encoding for Unicode
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Translation file '{filepath}' not found. Using default English.")
            return {} # Return empty dict if file not found
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in '{filepath}'. Check the file.")
            return {} # Return empty dict if JSON is invalid


    def get_translation(self, key, language_code=None):
        """Retrieves translation for a given key and language code."""
        lang_code_to_use = language_code or self.current_language # Use provided code or current language
        lang_data = self.translations.get(lang_code_to_use, {}) # Get language data or empty dict if not found
        return lang_data.get(key, f"<{key}>") # Return translation or key in brackets if missing


    def set_language(self, language_code):
        """Sets the current language and updates UI text."""
        if language_code in self.translations:
            self.current_language = language_code
            self.update_ui_text()
        else:
            print(f"Warning: Language code '{language_code}' not found in translations.")

    def update_ui_text(self):
        """Updates all translatable text elements in the UI."""
        # Notebook Tabs
        self.notebook.tab(0, text=self.get_translation("tab_process"))
        self.notebook.tab(1, text=self.get_translation("tab_help"))

        # Process Tab elements
        self.input_frame.config(text=self.get_translation("table_input_files.lbl_title"))
        self.input_list.heading("Path", text=self.get_translation("table_input_files.col_file_path"))
        self.input_list.heading("File name", text=self.get_translation("table_input_files.col_file_name"))
        self.input_list.heading("Size", text=self.get_translation("table_input_files.col_file_size"))
        self.browse_button.config(text=self.get_translation("table_input_files.btn_browse"))
        self.clear_button.config(text=self.get_translation("table_input_files.btn_clear"))
        self.output_frame.config(text=self.get_translation("table_output_files.lbl_title"))
        self.output_list.heading("File name", text=self.get_translation("table_output_files.col_file_name"))
        self.output_list.heading("Size", text=self.get_translation("table_output_files.col_file_size"))
        self.output_button.config(text=self.get_translation("table_output_files.btn_choose_dir"))
        self.arrow_button.config(text=self.get_translation("btn_process")) # Assuming you want to translate the arrow button text too

        # Help Tab elements (if any translatable text is added there later)
        # Example (if you add a label with help text and give it id_str="help_tab.help_label"):
        # if hasattr(self.help_label, 'id_str') and self.help_label.id_str == "help_tab.help_label":
        #     self.help_label.config(text=self.get_translation("help_tab.help_label"))


    def create_process_tab(self):

        self.input_frame = ttk.LabelFrame(self.process_frame, text=self.get_translation("table_input_files.lbl_title")) # Get translated title
        self.input_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.input_frame.id_str = "table_input_files.lbl_title" # Assign ID

        self.input_list = ttk.Treeview(self.input_frame, columns=("Path", "File name", "Size", "Item ID", "Delete"), show="headings")
        self.input_list.heading("Path", text=self.get_translation("table_input_files.col_file_path")) # Get translated heading
        self.input_list.heading("File name", text=self.get_translation("table_input_files.col_file_name")) # Get translated heading
        self.input_list.heading("Size", text=self.get_translation("table_input_files.col_file_size")) # Get translated heading
        self.input_list.heading("Item ID", text="Item ID")
        self.input_list.heading("Delete", text="")
        self.input_list.column("Item ID", width=0, stretch=tk.NO)
        self.input_list.column("Delete", width=30, anchor="center")
        self.input_list.pack(expand=True, fill="both", padx=5, pady=5)
        self.input_list.tag_configure("hidden_id", foreground="#d9d9d9")

        self.input_list.unbind("<<TreeviewSelect>>")

        buttons_frame = ttk.Frame(self.input_frame)
        buttons_frame.pack(pady=5)

        self.browse_button = ttk.Button(buttons_frame, text=self.get_translation("table_input_files.btn_browse"), command=self.browse_files) # Get translated text
        self.browse_button.pack(side=tk.LEFT, padx=5)
        self.browse_button.id_str = "table_input_files.btn_browse" # Assign ID

        self.clear_button = ttk.Button(buttons_frame, text=self.get_translation("table_input_files.btn_clear"), command=self.clear_input_list) # Get translated text
        self.clear_button.pack(side=tk.LEFT, padx=5)
        self.clear_button.id_str = "table_input_files.btn_clear" # Assign ID

        # Right-click context menu for input list
        self.input_list.bind("<Button-3>", self.show_input_context_menu)

        self.arrow_button = ttk.Button(self.process_frame, text=self.get_translation("btn_process"),  width=5, command=self.start_processing_threads) # Get translated text
        self.arrow_button.pack(side=tk.LEFT, padx=20)
        self.arrow_button.id_str = "btn_process" # Assign ID
        # Style for hover effect (using ttk.Style)
        style = ttk.Style()
        style.map("Arrow.TButton",
                  foreground=[("active", "blue")],
                  background=[("active", "lightgray")])
        self.arrow_button.configure(style="Arrow.TButton")

        self.output_frame = ttk.LabelFrame(self.process_frame, text=self.get_translation("table_output_files.lbl_title")) # Get translated title
        self.output_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.output_frame.id_str = "table_output_files.lbl_title" # Assign ID

        default_output_dir = pathlib.Path("./output").resolve()
        self.output_path_var = tk.StringVar(value=str(default_output_dir))
        output_path_label = ttk.Label(self.output_frame, textvariable=self.output_path_var, wraplength=150)
        output_path_label.pack(pady=5)

        self.output_button = ttk.Button(self.output_frame, text=self.get_translation("table_output_files.btn_choose_dir"), command=self.choose_output_directory) # Get translated text
        self.output_button.pack()
        self.output_button.id_str = "table_output_files.btn_choose_dir" # Assign ID

        self.output_list = ttk.Treeview(self.output_frame, columns=("File name", "Size"), show="headings")
        self.output_list.heading("File name", text=self.get_translation("table_output_files.col_file_name")) # Get translated heading
        self.output_list.heading("Size", text=self.get_translation("table_output_files.col_file_size")) # Get translated heading
        self.output_list.pack(expand=True, fill="both", padx=5, pady=5)


    def create_help_tab(self):
        help_text_en = """
        Instructions:

        1.  **Input Files:**  Click 'Browse' to select image files or a directory.
        2.  **Output Directory:**  Click '...' next to the output path to choose where the PDFs will be saved.  The default is './output'.
        3.  **Process:**  Click the arrow button (➡) to start the conversion.
        4.  **Progress Bar:**  Shows the progress of the conversion.

        This program uses EasyOCR to extract text from images and creates searchable PDFs.
        """
        self.help_label = ttk.Label(self.help_frame, text=self.get_translation("help_tab.help_label")) # Get translated text
        self.help_label.pack(padx=20, pady=20)
        self.help_label.id_str = "help_tab.help_label" # Assign ID # Assign ID

    def show_input_context_menu(self, event):
        """Shows a context menu for deleting selected items in the input list."""
        try:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Delete", command=self.delete_selected_input_items)

            # Get item clicked on (if any)
            item = self.input_list.identify_row(event.y)
            if item:
                # Select the item if it's not already selected
                if item not in self.input_list.selection():
                    self.input_list.selection_set(item)

                menu.tk_popup(event.x_root, event.y_root)

        finally:
            menu.grab_release()

    def delete_selected_input_items(self):
        """Deletes the selected items from the input list."""
        selected_items = self.input_list.selection()
        for item in selected_items:
            self.input_list.delete(item)
        if not self.input_list.get_children():
            self.hide_progress()

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        if file_paths:
            for path in file_paths:
                file_path = pathlib.Path(path)
                file_size = file_path.stat().st_size
                item_id = self.input_list.insert("", "end", values=(file_path, file_path.name, file_size, "", "")) # Added empty string for Item ID initially
                self.input_list.set(item_id, "Item ID", item_id) # Set the actual item ID in the hidden column
                # Create the delete button *after* inserting the item, and use a lambda
                delete_button = ttk.Button(self.input_list, text="X", width=3,
                                            command=lambda item=item_id: self.delete_input_item(item))
                # Place the button in the "Delete" column of the Treeview
                self.input_list.set(item_id, "Delete", "")
                self.input_list.item(item_id, tags=("delete_button",))
                # Bind to the delete button's tag
                self.input_list.tag_bind("delete_button", "<Button-1>",
                                          lambda e, item=item_id: self.on_delete_button_click(e, item))
            self.show_progress()

    def on_delete_button_click(self, event, item_id):
        """Handles a click on the delete button within the Treeview."""
        clicked_element = self.input_list.identify_element(event.x, event.y)
        if "button" in clicked_element:
             self.delete_input_item(item_id)

    def delete_input_item(self, item_id):
        """Deletes a single item from the input list."""
        self.input_list.delete(item_id)
        if not self.input_list.get_children():
            self.hide_progress()

    def clear_input_list(self):
        for item in self.input_list.get_children():
            self.input_list.delete(item)
        self.hide_progress()

    def choose_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_path_var.set(directory)

    def show_progress(self):
        self.progress_bar.pack(pady=10)
        self.progress_label.pack()

    def hide_progress(self):
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"{value}%")
        self.root.update_idletasks()


    def start_processing_threads(self):
        output_dir = pathlib.Path(self.output_path_var.get())
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            log(f"Created output directory: {output_dir}")

        total_files = len(self.input_list.get_children())
        if total_files == 0:
            messagebox.showwarning("No Files", "Please select files to process.")
            return

        self.progress_bar["maximum"] = total_files
        self.progress_bar["value"] = 0
        self.files_processed = 0
        self.show_progress()

        log(f"Starting PDF conversion with threads. Total files: {total_files}")

        self.processing_queue = queue.Queue() # Create a new queue for each batch
        self.arrow_button.config(state=tk.DISABLED) # Disable process button
        self.root.config(cursor="wait") # Change cursor to wait

        for item_id in self.input_list.get_children():
            file_path = self.input_list.item(item_id)["values"][0]
            log(f"Processing file [Threaded]: {file_path}")

            thread = threading.Thread(target=self.process_image_thread, args=(file_path, output_dir, self.processing_queue, item_id)) # Pass item_id
            thread.daemon = True
            thread.start()

        self.check_processing_queue()


    def process_image_thread(self, file_path, output_dir, task_queue, item_id): # Added item_id
        """Worker function to process a single image in a separate thread."""
        try:
            draw_bounds_before_process(file_path, output_dir)
            img_to_pdf(file_path, output_dir)
            task_queue.put(item_id) # Put item_id in queue on success
        except Exception as e:
            log(f"Error processing file {file_path}: {e}", error=True)
            task_queue.put(None) # Put None in queue on error


    def check_processing_queue(self):
        """Checks the processing queue for completed tasks and updates progress."""
        try:
            while True:
                item_id_processed = self.processing_queue.get_nowait() # Get item_id (or None for error)
                if item_id_processed is not None: # Successful processing
                    self.files_processed += 1
                    progress_percent = (self.files_processed / self.progress_bar["maximum"]) * 100
                    self.update_progress(progress_percent)
                    log(f"File processed. Progress: {progress_percent:.2f}%")

                    # Move item from input to output list
                    item_values = self.input_list.item(item_id_processed)["values"]
                    file_name = item_values[1] # File name is in the 2nd column
                    file_size = item_values[2] # File size is in the 3rd column
                    self.output_list.insert("", "end", values=(file_name, file_size)) # Insert into output list
                    self.input_list.delete(item_id_processed) # Delete from input list

                else:
                    log("File processing reported an error (check logs)") # Handle error signal if needed

                self.processing_queue.task_done()

        except queue.Empty:
            pass

        if self.files_processed < self.progress_bar["maximum"]:
            self.root.after(100, self.check_processing_queue)
        else:
            log("PDF conversion batch finished.")
            messagebox.showinfo("Conversion Complete", "All images converted to PDF!") # Show message box
            self.arrow_button.config(state=tk.NORMAL) # Re-enable process button
            self.root.config(cursor="") # Revert cursor to default
            if not self.input_list.get_children(): # Hide progress bar if input list is now empty
                self.hide_progress()


session_date = time.strftime("%Y-%m-%d_%H-%M-%S")

def log(message, error=False):
    log_file = assert_log_file()
    t = time.strftime("%Y-%m-%d %H:%M:%S")

    if not (error):
        print(f"[ {t} ] {message}")
        with log_file.open("a") as f:
            f.write(f"[ {t} ] {message}\n")
    else:
        print(f"[ {t} ] {message}")
        with log_file.open("a") as f:
             f.write(f"[ {t} ] {message}\n")
        traceback.print_exc()
        with log_file.open("a") as f:
            traceback.print_exc(file=f)

def assert_log_file():
    global session_date

    log_dir = pathlib.Path("./logs")

    if not log_dir.exists():
        log_dir.mkdir()

    log_file = pathlib.Path(log_dir, f"log_{session_date}.txt")

    if not log_file.exists():
        log_file.touch()

    return log_file

def main():
    log_file = assert_log_file()

    root = tk.Tk()
    gui = Img2PdfGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()