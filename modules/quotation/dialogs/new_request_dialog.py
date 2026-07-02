import customtkinter as ctk
from tkcalendar import DateEntry
from modules.quotation.services.quotation_service import create_material_request


class NewRequestDialog(ctk.CTkToplevel):
    def __init__(self, parent,user):
        
        super().__init__(parent)
        self.user = user

        self.title("New Material Request")
        self.geometry("650x620")
        self.resizable(False, False)
        self.grab_set()

        self.build_ui()

    def build_ui(self):
        self.configure(fg_color="#F5F7FA")

        title = ctk.CTkLabel(
            self,
            text="New Material Request",
            font=("Segoe UI", 24, "bold"),
            text_color="#0A2E63"
        )
        title.pack(pady=(25, 15))

        form = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        form.pack(fill="both", expand=True, padx=30, pady=10)

        self.project_entry = self.add_entry(form, "Project Name")
        self.description_entry = self.add_entry(form, "Material Request Name / Description")
        self.requested_by_entry = self.add_entry(form, "Requested By")
        self.assigned_to_entry = self.add_entry(form, "Assigned To")

        self.priority_option = self.add_option(
            form,
            "Priority",
            ["High", "Medium", "Low"]
        )

        self.status_option = self.add_option(
            form,
            "Status",
            ["New", "Assigned", "In Progress", "Waiting Supplier Quote", "Completed", "Archived"]
        )

        ctk.CTkLabel(
            form,
            text="Due Date",
            font=("Segoe UI", 13, "bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=30, pady=(10, 3))

        self.due_date_entry = DateEntry(form, width=25, date_pattern="yyyy-mm-dd")
        self.due_date_entry.pack(anchor="w", padx=30, pady=(0, 10))

        ctk.CTkLabel(
            form,
            text="Remarks",
            font=("Segoe UI", 13, "bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=30, pady=(10, 3))

        self.remarks_box = ctk.CTkTextbox(form, width=540, height=90)
        self.remarks_box.pack(padx=30, pady=(0, 15))

        button_frame = ctk.CTkFrame(form, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Save Request",
            width=160,
            height=40,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.save_request
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=40,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.destroy
        ).pack(side="left", padx=10)

    def add_entry(self, parent, label):
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 13, "bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=30, pady=(10, 3))

        entry = ctk.CTkEntry(parent, width=540, height=38)
        entry.pack(padx=30, pady=(0, 5))
        return entry

    def add_option(self, parent, label, values):
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 13, "bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=30, pady=(10, 3))

        option = ctk.CTkOptionMenu(parent, width=540, height=38, values=values)
        option.pack(padx=30, pady=(0, 5))
        option.set(values[0])
        return option

    def save_request(self):
        data = {
        "project": self.project_entry.get().strip(),
        "description": self.description_entry.get().strip(),
        "requested_by": self.requested_by_entry.get().strip(),
        "assigned_to": self.assigned_to_entry.get().strip(),
        "priority": self.priority_option.get(),
        "status": self.status_option.get(),
        "due_date": self.due_date_entry.get_date().strftime("%Y-%m-%d"),
        "remarks": self.remarks_box.get("1.0", "end").strip()
        }

        if not data["project"] or not data["description"]:
            print("Project and Description are required.")
            return

        request_no = create_material_request(data, self.user["id"])

        print(f"Material Request saved successfully: {request_no}")

        self.destroy()