import tkinter.messagebox as messagebox

def show_error(title: str, message: str) -> None:
    """Display an error message dialog."""
    messagebox.showerror(title, message)


def show_warning(title: str, message: str) -> None:
    """Display a warning message dialog."""
    messagebox.showwarning(title, message)


def show_info(title: str, message: str) -> None:
    """Display an informational message dialog."""
    messagebox.showinfo(title, message)
