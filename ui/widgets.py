import tkinter as tk


def create_button(parent, text, command, bg_color, fg_color="white"):
    """Cria um botão padronizado para a interface."""
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg=fg_color,
        font=("Segoe UI", 9, "bold"),
        padx=12,
        pady=8,
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
    )

    def on_enter(event):
        button.config(bg=adjust_color(bg_color, -15))

    def on_leave(event):
        button.config(bg=bg_color)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    return button


def adjust_color(hex_color, adjustment):
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    adjusted = tuple(max(0, min(255, value + adjustment)) for value in rgb)
    return f"#{adjusted[0]:02x}{adjusted[1]:02x}{adjusted[2]:02x}"
