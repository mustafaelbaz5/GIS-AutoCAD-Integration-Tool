"""Application entry point."""

import customtkinter as ctk


def main() -> None:
    """Launch the application window."""
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("GIS & AutoCAD Integration Tool")
    app.geometry("800x600")
    app.mainloop()


if __name__ == "__main__":
    main()
