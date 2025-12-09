import customtkinter as ctk

# -------------------------------------------------------------
# 1. Configuração inicial do tema
# -------------------------------------------------------------
ctk.set_appearance_mode("dark")         # Define tema escuro
ctk.set_default_color_theme("green")    # Define verde como cor principal

# -------------------------------------------------------------
# 2. Criar a janela principal
# -------------------------------------------------------------
janela = ctk.CTk()                      
janela.title("Barbearia Granada v1.0") 
janela.geometry("900x500")

# -------------------------------------------------------------
# 3. LISTAS DINÂMICAS (importante!)
# Aqui serão guardados todos os serviços e produtos adicionados.
# Cada item é salvo como: ("Nome", "Valor")
# -------------------------------------------------------------
servicos = []
produtos = []

# -------------------------------------------------------------
# 4. Criar o quadro da esquerda (menu de botões)
# -------------------------------------------------------------
frame_esquerda = ctk.CTkFrame(janela, width=200, corner_radius=10)
frame_esquerda.pack(side="left", fill="y", padx=10, pady=10)

# -------------------------------------------------------------
# FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO DA INTERFACE
# Sempre que um item é adicionado, essa função limpa os antigos
# e reexibe todos os serviços/produtos na tela.
# -------------------------------------------------------------
def atualizar_listas():
    # Limpa tudo dentro dos quadros
    for widget in lista_servicos.winfo_children():
        widget.destroy()
    for widget in lista_produtos.winfo_children():
        widget.destroy()

    # Recria os serviços atualizados
    for nome, valor in servicos:
        ctk.CTkLabel(lista_servicos, text=f"{nome} __________ R$ {valor}").pack(anchor="w", pady=2)

    # Recria os produtos atualizados
    for nome, valor in produtos:
        ctk.CTkLabel(lista_produtos, text=f"{nome} __________ R$ {valor}").pack(anchor="w", pady=2)

# -------------------------------------------------------------
# 5. Criar a janela de ADICIONAR item
# -------------------------------------------------------------
def abrir_janela_adicionar():
    janela_add = ctk.CTkToplevel(janela)
    janela_add.title("Adicionar Item")
    janela_add.geometry("350x300")

    # Título
    titulo = ctk.CTkLabel(janela_add, text="Adicionar Serviço ou Produto", font=("Arial", 16, "bold"))
    titulo.pack(pady=10)

    # Seleção: Serviço ou Produto
    tipo_var = ctk.StringVar(value="servico")  # valor padrão

    frame_radios = ctk.CTkFrame(janela_add)
    frame_radios.pack(pady=10)

    radio_servico = ctk.CTkRadioButton(frame_radios, text="Serviço", variable=tipo_var, value="servico")
    radio_servico.pack(side="left", padx=10)

    radio_produto = ctk.CTkRadioButton(frame_radios, text="Produto", variable=tipo_var, value="produto")
    radio_produto.pack(side="left", padx=10)

    # Campo para nome
    label_nome = ctk.CTkLabel(janela_add, text="Nome:")
    label_nome.pack(anchor="w", padx=20)

    entrada_nome = ctk.CTkEntry(janela_add, width=250, placeholder_text="Ex: Corte degradê, Gel, Camisa...")
    entrada_nome.pack(pady=5)

    # Campo para valor
    label_valor = ctk.CTkLabel(janela_add, text="Valor (R$):")
    label_valor.pack(anchor="w", padx=20)

    entrada_valor = ctk.CTkEntry(janela_add, width=150, placeholder_text="Ex: 25.00")
    entrada_valor.pack(pady=5)

    # Função interna do botão "Salvar"
    def salvar_item():
        tipo = tipo_var.get()
        nome = entrada_nome.get().strip()
        valor = entrada_valor.get().strip()

        # Validação simples
        if nome == "" or valor == "":
            ctk.CTkMessageBox(title="Erro", message="Preencha todos os campos!")
            return

        # Armazena nas listas corretas
        if tipo == "servico":
            servicos.append((nome, valor))
        else:
            produtos.append((nome, valor))

        # Atualiza a interface do quadro direito
        atualizar_listas()

        # Fecha a janela
        janela_add.destroy()

    # Botão salvar
    botao_salvar = ctk.CTkButton(janela_add, text="Salvar", command=salvar_item)
    botao_salvar.pack(pady=20)

# -------------------------------------------------------------
# 6. Botões do menu esquerdo
# -------------------------------------------------------------
botao_adicionar = ctk.CTkButton(frame_esquerda, text="Adicionar", command=abrir_janela_adicionar)
botao_adicionar.pack(fill="x", pady=5)

botao_editar = ctk.CTkButton(frame_esquerda, text="Editar")
botao_editar.pack(fill="x", pady=5)

botao_remover = ctk.CTkButton(frame_esquerda, text="Remover")
botao_remover.pack(fill="x", pady=5)

# -------------------------------------------------------------
# 7. Criar o quadro da direita (lista de serviços e produtos)
# -------------------------------------------------------------
frame_direita = ctk.CTkFrame(janela, corner_radius=10)
frame_direita.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# 8. Título SERVIÇOS
label_servicos = ctk.CTkLabel(frame_direita, text="SERVIÇOS", font=("Arial", 18, "bold"))
label_servicos.pack(anchor="nw", pady=(10, 5), padx=10)

# 9. Área onde os serviços serão exibidos dinamicamente
lista_servicos = ctk.CTkFrame(frame_direita, corner_radius=8)
lista_servicos.pack(fill="x", padx=15, pady=5)

# 10. Título PRODUTOS
label_produtos = ctk.CTkLabel(frame_direita, text="PRODUTOS", font=("Arial", 18, "bold"))
label_produtos.pack(anchor="nw", pady=(20, 5), padx=10)

# 11. Área onde os produtos serão exibidos dinamicamente
lista_produtos = ctk.CTkFrame(frame_direita, corner_radius=8)
lista_produtos.pack(fill="x", padx=15, pady=5)

# -------------------------------------------------------------
# 12. Iniciar o loop principal da interface
# -------------------------------------------------------------
janela.mainloop()
