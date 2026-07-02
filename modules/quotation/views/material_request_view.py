import customtkinter as ctk


class MaterialRequestView(ctk.CTkFrame):
    def __init__(self, parent, user, on_back=None):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)

        self.user = user
        self.on_back = on_back

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_toolbar()
        self.build_request_info()
        self.build_items_section()

    def build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            toolbar,
            text="New Material Request",
            font=("Segoe UI", 24, "bold"),
            text_color="#0A2E63"
        )
        title.pack(side="left", padx=20, pady=15)

        back_btn = ctk.CTkButton(
            toolbar,
            text="Back",
            width=100,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.on_back
        )
        back_btn.pack(side="right", padx=10)

        save_btn = ctk.CTkButton(
            toolbar,
            text="Save",
            width=120,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.save_request
        )
        save_btn.pack(side="right", padx=10)

    def build_request_info(self):
        section = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        section.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        section.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            section,
            text="Request Information",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63"
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 10))

        self.project_entry = self.add_field(section, "Project / Site", 1, 0)
        self.client_entry = self.add_field(section, "Client", 1, 1)
        self.assigned_to_entry = self.add_field(section, "Assigned To", 1, 2)

        self.priority_option = self.add_option(
            section,
            "Priority",
            ["High", "Medium", "Low"],
            1,
            3
        )

        self.due_date_entry = self.add_field(section, "Due Date (YYYY-MM-DD)", 3, 0)

        self.status_option = self.add_option(
            section,
            "Status",
            [
                "New",
                "Assigned",
                "In Progress",
                "Waiting Supplier Quote",
                "Completed",
                "Archived"
            ],
            3,
            1
        )

        self.remarks_entry = self.add_field(section, "Remarks", 3, 2, columnspan=2)

    def build_items_section(self):
        section = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        section.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(section, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="Material Items",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Add Item",
            width=120,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.add_item_row
        ).pack(side="right")

        self.items_frame = ctk.CTkScrollableFrame(
            section,
            fg_color="#F5F7FA",
            corner_radius=10
        )
        self.items_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.item_rows = []
        self.add_item_row()

    def add_item_row(self):
        row_frame = ctk.CTkFrame(self.items_frame, fg_color="#FFFFFF", corner_radius=10)
        row_frame.pack(fill="x", padx=10, pady=6)

        qty = ctk.CTkEntry(row_frame, width=80, placeholder_text="Qty")
        qty.pack(side="left", padx=6, pady=10)

        unit = ctk.CTkEntry(row_frame, width=90, placeholder_text="Unit")
        unit.pack(side="left", padx=6, pady=10)

        desc = ctk.CTkEntry(row_frame, width=360, placeholder_text="Material Description")
        desc.pack(side="left", padx=6, pady=10)

        brand = ctk.CTkEntry(row_frame, width=140, placeholder_text="Brand")
        brand.pack(side="left", padx=6, pady=10)

        remarks = ctk.CTkEntry(row_frame, width=220, placeholder_text="Remarks")
        remarks.pack(side="left", padx=6, pady=10)

        delete_btn = ctk.CTkButton(
            row_frame,
            text="Delete",
            width=80,
            fg_color="#E53935",
            hover_color="#B71C1C",
            command=lambda: self.delete_item_row(row_frame)
        )
        delete_btn.pack(side="right", padx=10, pady=10)

        self.item_rows.append({
            "frame": row_frame,
            "qty": qty,
            "unit": unit,
            "description": desc,
            "brand": brand,
            "remarks": remarks
        })

    def delete_item_row(self, row_frame):
        self.item_rows = [
            row for row in self.item_rows
            if row["frame"] != row_frame
        ]
        row_frame.destroy()

    def add_field(self, parent, label, row, column, columnspan=1):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827"
        ).grid(row=0, column=0, sticky="w")

        entry = ctk.CTkEntry(wrapper, height=36)
        entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        return entry

    def add_option(self, parent, label, values, row, column):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827"
        ).grid(row=0, column=0, sticky="w")

        option = ctk.CTkOptionMenu(wrapper, values=values, height=36)
        option.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        option.set(values[0])

        return option

    def save_request(self):
        items = []

        for row in self.item_rows:
            description = row["description"].get().strip()

            if not description:
                continue

            items.append({
                "quantity": row["qty"].get().strip(),
                "unit": row["unit"].get().strip(),
                "description": description,
                "brand": row["brand"].get().strip(),
                "remarks": row["remarks"].get().strip()
            })

        data = {
            "project": self.project_entry.get().strip(),
            "client": self.client_entry.get().strip(),
            "assigned_to": self.assigned_to_entry.get().strip(),
            "priority": self.priority_option.get(),
            "status": self.status_option.get(),
            "due_date": self.due_date_entry.get().strip(),
            "remarks": self.remarks_entry.get().strip(),
            "items": items
        }

        print("Material Request Workspace Data:")
        print(data)