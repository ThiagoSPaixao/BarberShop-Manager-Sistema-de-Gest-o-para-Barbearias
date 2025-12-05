import customtkinter as ctk

# 1. Configuração inicial do tema
ctk.set_appearance_mode("dark")         # Define tema escuro
ctk.set_default_color_theme("green")    # Define verde como cor principal

# 2. Criar a janela principal
janela = ctk.CTk()                      # Cria a janela
janela.title("Barbearia Granada v1.0")       # Título da janela
janela.geometry("900x500")              # Largura x Altura

# 3. Iniciar o loop da interface
janela.mainloop()
