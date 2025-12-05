import customtkinter as ctk

# 1. Configuração inicial do tema
ctk.set_appearance_mode("dark")         # Define tema escuro
ctk.set_default_color_theme("green")    # Define verde como cor principal

# 2. Criar a janela principal
janela = ctk.CTk()                      # Cria a janela
janela.title("Barbearia Granada v1.0")       # Título da janela
janela.geometry("900x500")             # Largura x Altura

# 4. Criar o quadro da esquerda (menu de botões)
frame_esquerda = ctk.CTkFrame(janela, width=200, corner_radius=10)
frame_esquerda.pack(side="left", fill="y", padx=10, pady=10)

# 5. Botão Adicionar
botao_adicionar = ctk.CTkButton(frame_esquerda, text="Adicionar")
botao_adicionar.pack(fill="x", pady=5)

# 6. Botão Editar
botao_editar = ctk.CTkButton(frame_esquerda, text="Editar")
botao_editar.pack(fill="x", pady=5)

# 6. Botão Remover
botao_remover = ctk.CTkButton(frame_esquerda, text="Remover")
botao_remover.pack(fill="x", pady=5)






#Iniciar o loop da interface
janela.mainloop()
