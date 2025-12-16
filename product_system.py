import csv
from datetime import date
import os
from typing import List, Dict
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.constants import VERTICAL, NW, Y, BOTH, YES

# --- Configuration ---
CSV_FILENAME = 'product_master_data.csv'
DATE_FORMAT = '%Y-%m-%d'

# --- 1. Product Master Data Class ---
class Product:
    """Represents a product with extensive master data and handles shelf-life calculation."""

    def __init__(self, **kwargs):
        # A list of all expected fields
        self.fields = [
            "Status", "SKU Code", "SKU Name", "Product Line", "Category", 
            "Sub-Category", "MFUPC", "SRP", "PCS per Inner Box", 
            "PCS per Master Box", "Shelflife (Months)", "Period After Opening (Months)", 
            "CBM", "Height(cm)", "Width(cm)", "Length(cm)", 
            "Weight(g)", "Expiry Item", "Selling Ban", "Storage Type", 
            "Tester product", "Image URL"
        ]
        
        # Dictionary mapping the original field names to their cleaned attribute names
        self.attr_map = {} 
        
        # 1. Dynamically set attributes and record the cleaned names
        for field in self.fields:
            # Clean name: replaces spaces/hyphens with underscores, and removes (cm)/(g)/(Months) units
            attr_name = field.replace(' ', '_').replace('-', '_').replace('(cm)', 'cm').replace('(g)', 'g').replace('(Months)', 'Months')
            setattr(self, attr_name, kwargs.get(field, ""))
            self.attr_map[field] = attr_name

        # 2. Type conversion for numerical/integer fields (USING THE CORRECTED ATTRIBUTE NAMES)
        
        # Floats
        self.SRP = self._try_float(self.SRP)
        self.CBM = self._try_float(self.CBM)
        self.Heightcm = self._try_float(self.Heightcm) # Fixed: Heightcm
        self.Widthcm = self._try_float(self.Widthcm)
        self.Lengthcm = self._try_float(self.Lengthcm)
        self.Weightg = self._try_float(self.Weightg)
        
        # Integers
        self.PCS_per_Inner_Box = self._try_int(self.PCS_per_Inner_Box)
        self.PCS_per_Master_Box = self._try_int(self.PCS_per_Master_Box)
        self.Shelflife_Months = self._try_int(self.Shelflife_Months) # FIXED: Shelflife_Months
        self.Period_After_Opening_Months = self._try_int(self.Period_After_Opening_Months) # Fixed: Period_After_Opening_Months


    def _try_float(self, value):
        try:
            return float(value) if value else 0.0
        except ValueError:
            return 0.0

    def _try_int(self, value):
        try:
            return int(value) if value else 0
        except ValueError:
            return 0

    def get_data_for_display(self):
        """Returns key data fields as a list for display in the Treeview."""
        return [
            getattr(self, "SKU_Code"),
            getattr(self, "SKU_Name"),
            getattr(self, "Status"),
            getattr(self, "Product_Line"),
            getattr(self, "Category"),
            f"₱{getattr(self, 'SRP'):,.2f}", # Formatted SRP
            f"{getattr(self, 'Shelflife_Months')} months",
            getattr(self, "Storage_Type")
        ]
    
    def get_data_for_csv(self):
        """Returns all data fields as a dictionary for CSV saving."""
        data = {}
        for field in self.fields:
            # Use the same name cleaning logic to retrieve the attribute
            attr_name = field.replace(' ', '_').replace('-', '_').replace('(cm)', 'cm').replace('(g)', 'g').replace('(Months)', 'Months')
            data[field] = getattr(self, attr_name)
        return data

# --- 2. Analytical Functions (Dashboard Logic) ---

def analyze_products(db: List['Product']) -> Dict[str, str]:
    """Calculates key analytical metrics for the dashboard."""
    total_products = len(db)
    active_count = 0
    discontinued_count = 0
    total_srp = 0
    product_line_counts = {}

    if total_products == 0:
        return {
            "Total Products": "0", "Active Products": "0", "Discontinued": "0", 
            "Avg SRP": "N/A", "Top Product Line": "N/A"
        }

    for product in db:
        if product.Status and product.Status.lower() == 'active':
            active_count += 1
        elif product.Status and product.Status.lower() == 'discontinued':
            discontinued_count += 1
            
        total_srp += product.SRP
        
        line = product.Product_Line if product.Product_Line else "Unassigned"
        product_line_counts[line] = product_line_counts.get(line, 0) + 1

    avg_srp = total_srp / total_products if total_products > 0 else 0
    
    # Safely find the top product line
    top_line = max(product_line_counts, key=product_line_counts.get) if product_line_counts else "N/A"

    return {
        "Total Products": str(total_products),
        "Active Products": str(active_count),
        "Discontinued": str(discontinued_count),
        "Avg SRP": f"₱{avg_srp:,.2f}",
        "Top Product Line": f"{top_line} ({product_line_counts.get(top_line, 0)})"
    }

# --- 3. Data Persistence (CSV Functions) ---

ProductDB = List['Product'] 
product_database: ProductDB = []

def save_products_to_csv():
    """Saves the current product database to the CSV file."""
    if not product_database:
        fieldnames = Product(**{}).fields 
    else:
        fieldnames = product_database[0].fields
        
    try:
        with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for product in product_database:
                writer.writerow(product.get_data_for_csv())
        return True
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred while saving: {e}")
        return False

def load_products_from_csv():
    """Loads products from the CSV file into the database list."""
    if not os.path.exists(CSV_FILENAME):
        return

    try:
        with open(CSV_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            loaded_products = []
            for row in reader:
                product = Product(**row)
                loaded_products.append(product)
            
            product_database[:] = loaded_products
    except Exception as e:
        messagebox.showerror("Load Error", f"An error occurred while loading data: {e}")

# --- 4. Tkinter GUI Application ---

class ProductApp:
    def __init__(self, master):
        self.master = master
        master.title("Advanced Product Master Data Manager")
        master.geometry("1000x700")

        # Get the list of fields from a correctly initialized product object
        self.product_fields = Product(**{}).fields 

        load_products_from_csv()

        self._create_input_frame()
        ttk.Button(self.master, text="📊 View Analytical Dashboard", command=self._show_dashboard).pack(pady=5)
        self._create_list_frame()
        
        self._refresh_product_list()
        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_input_frame(self):
        """Creates a scrollable section for adding new products (21 fields)."""
        input_labelframe = ttk.LabelFrame(self.master, text="➕ Product Master Data Input (21 Fields)", padding="10")
        input_labelframe.pack(padx=10, pady=10, fill="x")

        canvas = tk.Canvas(input_labelframe, height=180) 
        scrollbar = ttk.Scrollbar(input_labelframe, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill=Y)
        canvas.pack(side="left", fill=BOTH, expand=YES)
        
        self.entries = {}
        
        # Populate the scrollable form
        for i, field in enumerate(self.product_fields):
            row = i // 4 
            col = i % 4
            
            ttk.Label(scrollable_frame, text=field + ":").grid(row=row * 2, column=col, padx=5, pady=2, sticky="w")
            
            if field == "Status":
                options = ["Active", "Discontinued", "Pending"]
                entry = ttk.Combobox(scrollable_frame, values=options, width=18)
                entry.grid(row=row * 2 + 1, column=col, padx=5, pady=2)
                entry.set(options[0])
            elif field in ["Expiry Item", "Selling Ban", "Tester product"]:
                options = ["Yes", "No"]
                entry = ttk.Combobox(scrollable_frame, values=options, width=18)
                entry.grid(row=row * 2 + 1, column=col, padx=5, pady=2)
                entry.set(options[1])
            else:
                entry = ttk.Entry(scrollable_frame, width=20)
                entry.grid(row=row * 2 + 1, column=col, padx=5, pady=2)
                
            self.entries[field] = entry

        # --- Action Buttons ---
        action_frame = ttk.Frame(input_labelframe)
        action_frame.pack(fill="x", pady=10)
        
        ttk.Button(action_frame, text="Add Product", command=self._add_product_gui).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Save Data", command=lambda: self._on_save(show_message=True)).pack(side=tk.LEFT, padx=10)


    def _create_list_frame(self):
        """Creates the section to display key product data in a table (Treeview)."""
        list_frame = ttk.LabelFrame(self.master, text="📋 Key Product Data Overview", padding="10")
        list_frame.pack(padx=10, pady=5, fill="both", expand=True)

        columns = ("sku_code", "sku_name", "status", "product_line", "category", "srp", "shelflife", "storage_type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        self.tree.heading("sku_code", text="SKU Code")
        self.tree.heading("sku_name", text="SKU Name")
        self.tree.heading("status", text="Status")
        self.tree.heading("product_line", text="Product Line")
        self.tree.heading("category", text="Category")
        self.tree.heading("srp", text="SRP (₱)")
        self.tree.heading("shelflife", text="Shelf-life")
        self.tree.heading("storage_type", text="Storage Type")

        self.tree.column("sku_code", width=100)
        self.tree.column("sku_name", width=180)
        self.tree.column("status", width=80)
        self.tree.column("srp", width=80, anchor='e') 

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _refresh_product_list(self):
        """Clears the Treeview and repopulates it with current database items."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for product in product_database:
            self.tree.insert('', tk.END, values=product.get_data_for_display())

    def _add_product_gui(self):
        """Handles the 'Add Product' button click."""
        
        product_data = {field: self.entries[field].get() for field in self.product_fields}

        if not product_data.get("SKU Code") or not product_data.get("SKU Name"):
            messagebox.showerror("Input Error", "SKU Code and SKU Name are required fields.")
            return

        try:
            new_product = Product(**product_data)
            product_database.append(new_product)
            
            self._refresh_product_list()
            messagebox.showinfo("Success", f"Product '{new_product.SKU_Name}' added successfully.")
            
            for field, entry in self.entries.items():
                if field not in ["Status", "Expiry Item", "Selling Ban", "Tester product"]:
                    entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during creation: {e}")

    def _on_save(self, show_message=False):
        """Saves data and optionally shows a confirmation message."""
        if save_products_to_csv():
            if show_message:
                messagebox.showinfo("Success", f"Data saved successfully to {CSV_FILENAME}.")
            return True
        return False
        
    def _on_closing(self):
        """Handles closing the window, prompting user to save."""
        if messagebox.askyesno("Exit System", "Do you want to save the current data before exiting?"):
            if self._on_save():
                self.master.destroy()
        else:
            self.master.destroy()

    def _show_dashboard(self):
        """Creates and displays the analytical dashboard window."""
        metrics = analyze_products(product_database)

        dashboard_window = tk.Toplevel(self.master)
        dashboard_window.title("Product Master Data Analytics")
        dashboard_window.geometry("550x300")
        dashboard_window.resizable(False, False)

        ttk.Label(dashboard_window, text="Master Data Analysis Summary", font=("Helvetica", 16, "bold")).pack(pady=10)

        metrics_frame = ttk.Frame(dashboard_window, padding="15")
        metrics_frame.pack(padx=10, pady=10)

        metric_data = [
            ("Total Products", metrics["Total Products"], "blue"),
            ("Active Products", metrics["Active Products"], "green"),
            ("Discontinued", metrics["Discontinued"], "red"),
            ("Average SRP", metrics["Avg SRP"], "purple"),
            ("Top Product Line", metrics["Top Product Line"], "orange"),
        ]
        
        for i, (label_text, value, color) in enumerate(metric_data):
            row = i // 3 
            col = i % 3
            
            card_frame = ttk.LabelFrame(metrics_frame, text=label_text, padding="10")
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            value_label = ttk.Label(card_frame, text=value, font=("Helvetica", 14, "bold"), foreground=color)
            value_label.pack(pady=5)
            
            metrics_frame.grid_columnconfigure(col, weight=1)
            metrics_frame.grid_rowconfigure(row, weight=1)


# --- 5. Main Execution ---

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductApp(root)
    root.mainloop()