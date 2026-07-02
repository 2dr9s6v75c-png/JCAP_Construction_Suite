class NavigationService:
    def __init__(self, workspace):
        self.workspace = workspace
        self.history = []

    def clear_workspace(self):
        for widget in self.workspace.winfo_children():
            widget.destroy()

    def navigate(self, view_class, *args, add_to_history=True, **kwargs):
        if add_to_history:
            self.history.append((view_class, args, kwargs))

        self.clear_workspace()

        view = view_class(self.workspace, *args, **kwargs)
        view.pack(fill="both", expand=True)

        return view

    def back(self):
        if len(self.history) <= 1:
            return

        self.history.pop()
        view_class, args, kwargs = self.history[-1]

        self.clear_workspace()

        view = view_class(self.workspace, *args, **kwargs)
        view.pack(fill="both", expand=True)

        return view