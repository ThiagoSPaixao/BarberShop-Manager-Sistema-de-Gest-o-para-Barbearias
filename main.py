import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------
# 1) Criando a janela principal
# ---------------------------------------------------------

janela = tk.Tk()                                #Aqui, estou criando a janela principal
janela.title("Barbearia Granada")               #Aqui, eu defini o título da minha janela
janela.geometry("900x500")                      #Largura x Altura da minha janela
janela.configure(bg="#3A4A3F")                #Defini a cor de fundo (Verde Oliva Militar)

# ---------------------------------------------------------
# 2) Criar o frame da esquerda (onde ficarão os botões)
# ---------------------------------------------------------

frame_esquerda = tk.Frame(janela, bg="#2F2F2F", width=200)
frame_esquerda.pack(side="left", fill="y")

# ---------------------------------------------------------
# 3) Criar o frame da direita (onde ficarão serviços e produtos)
# ---------------------------------------------------------

frame_direita = tk.Frame(janela, bg="#F1F1F1")
frame_direita.pack(side="right", fill="both", expand=True)

# ---------------------------------------------------------
# 4) Criar os botões do lado esquerdo
# ---------------------------------------------------------

btn_adicionar = tk.Button(
    frame_esquerda,
    text="Adicionar",
    bg="#556B2F",          # Verde militar
    fg="white",
    font=("Arial", 12, "bold"),
    padx=10, pady=5
)
btn_adicionar.pack(pady=10, fill="x")

btn_editar = tk.Button(
    frame_esquerda,
    text="Editar",
    bg="#C2A14A",          # Dourado fosco
    fg="black",
    font=("Arial", 12, "bold"),
    padx=10, pady=5
)
btn_editar.pack(pady=10, fill="x")

btn_remover = tk.Button(
    frame_esquerda,
    text="Remover",
    bg="#8B0000",          # Vermelho escuro militar
    fg="white",
    font=("Arial", 12, "bold"),
    padx=10, pady=5
)
btn_remover.pack(pady=10, fill="x")

# ---------------------------------------------------------
# 5) Títulos de Serviços e Produtos (lado direito)
# ---------------------------------------------------------

titulo_servicos = tk.Label(
    frame_direita,
    text="SERVIÇOS",
    bg="#F1F1F1",
    fg="black",
    font=("Arial", 16, "bold")
)
titulo_servicos.pack(pady=10)

lista_servicos = tk.Listbox(frame_direita, font=("Arial", 12), width=60, height=10)
lista_servicos.pack(pady=5)

titulo_produtos = tk.Label(
    frame_direita,
    text="PRODUTOS",
    bg="#F1F1F1",
    fg="black",
    font=("Arial", 16, "bold")
)
titulo_produtos.pack(pady=10)

lista_produtos = tk.Listbox(frame_direita, font=("Arial", 12), width=60, height=10)
lista_produtos.pack(pady=5)

# ---------------------------------------------------------
# 6) Iniciar o programa
# ---------------------------------------------------------
janela.mainloop()