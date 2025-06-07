import tkinter.messagebox as messagebox


def show_error(title: str, message: str) -> None:
    """Display an error dialog."""
    messagebox.showerror(title, message)


def show_warning(title: str, message: str) -> None:
    """Display a warning dialog."""
    messagebox.showwarning(title, message)


def show_info(title: str, message: str) -> None:
    """Display an information dialog."""
    messagebox.showinfo(title, message)
