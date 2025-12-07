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

# 7. Botão Remover
botao_remover = ctk.CTkButton(frame_esquerda, text="Remover")
botao_remover.pack(fill="x", pady=5)

# 8. Criar o quadro da direita (lista de serviços e produtos)
frame_direita = ctk.CTkFrame(janela, corner_radius=10)
frame_direita.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# 9. Título SERVIÇOS
label_servicos = ctk.CTkLabel(frame_direita, text="SERVIÇOS", font=("Arial", 18, "bold"))
label_servicos.pack(anchor="nw", pady=(10, 5), padx=10)

# 10. Lista estática de serviços (temporária)
lista_servicos = ctk.CTkFrame(frame_direita, corner_radius=8)
lista_servicos.pack(fill="x", padx=15, pady=5)

ctk.CTkLabel(lista_servicos, text="Corte Tesoura __________ R$ 22,00").pack(anchor="w", pady=2)
ctk.CTkLabel(lista_servicos, text="Corte Máquina  _________ R$ 20,00").pack(anchor="w", pady=2)
ctk.CTkLabel(lista_servicos, text="Máquina + Tesoura  ____ R$ 24,00").pack(anchor="w", pady=2)

# 11. Título PRODUTOS
label_produtos = ctk.CTkLabel(frame_direita, text="PRODUTOS", font=("Arial", 18, "bold"))
label_produtos.pack(anchor="nw", pady=(20, 5), padx=10)

# 12. Lista estática de produtos (temporária)
lista_produtos = ctk.CTkFrame(frame_direita, corner_radius=8)
lista_produtos.pack(fill="x", padx=15, pady=5)

ctk.CTkLabel(lista_produtos, text="Gel Capilar _____________ R$ 8,00").pack(anchor="w", pady=2)
ctk.CTkLabel(lista_produtos, text="Pomada Modeladora _______ R$ 25,00").pack(anchor="w", pady=2)
ctk.CTkLabel(lista_produtos, text="Espuma de Barbear _______ R$ 15,00").pack(anchor="w", pady=2)

# Função para abrir a janela de adicionar item
def abrir_janela_adicionar():
    janela_add = ctk.CTkToplevel(janela)
    janela_add.title("Adicionar Item")
    janela_add.geometry("350x300")

# Título
    titulo = ctk.CTkLabel(janela_add, text="Adicionar Serviço ou Produto", font=("Arial", 16, "bold"))
    titulo.pack(pady=10)


#Iniciar o loop da interface
janela.mainloop()
