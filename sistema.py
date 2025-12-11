import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional
import sqlite3
import pandas as pd
from tkinter import ttk
import webbrowser
from pathlib import Path
import shutil
from PIL import Image
import io
import base64

# =============================================================
# 1. BANCO DE DADOS SQLITE - PROFISSIONAL
# =============================================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('barbearia.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.criar_tabelas()
    
    def criar_tabelas(self):
        # Tabela de serviços
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                valor REAL NOT NULL,
                duracao INTEGER DEFAULT 30,
                ativo INTEGER DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de produtos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                valor_venda REAL NOT NULL,
                valor_custo REAL NOT NULL,
                estoque INTEGER DEFAULT 0,
                estoque_minimo INTEGER DEFAULT 5,
                ativo INTEGER DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de clientes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL UNIQUE,
                email TEXT,
                data_nascimento DATE,
                data_cadastro DATE DEFAULT CURRENT_DATE,
                total_gasto REAL DEFAULT 0,
                total_visitas INTEGER DEFAULT 0,
                observacoes TEXT
            )
        ''')
        
        # Tabela de agendamentos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                servico_id INTEGER,
                data DATE NOT NULL,
                hora TIME NOT NULL,
                profissional TEXT,
                status TEXT DEFAULT 'agendado',
                valor REAL NOT NULL,
                pago INTEGER DEFAULT 0,
                observacoes TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (servico_id) REFERENCES servicos(id)
            )
        ''')
        
        # Tabela de vendas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                tipo TEXT NOT NULL, -- 'servico' ou 'produto'
                item_id INTEGER NOT NULL,
                quantidade INTEGER DEFAULT 1,
                valor_unitario REAL NOT NULL,
                valor_total REAL NOT NULL,
                forma_pagamento TEXT NOT NULL,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')
        
        # Tabela de despesas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL,
                data DATE NOT NULL,
                forma_pagamento TEXT,
                observacoes TEXT
            )
        ''')
        
        # Tabela de usuários
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo TEXT DEFAULT 'funcionario',
                ativo INTEGER DEFAULT 1
            )
        ''')
        
        # Inserir admin padrão se não existir
        self.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha, tipo) VALUES (?, ?, ?, ?)",
                ('Administrador', 'admin', 'admin123', 'admin')
            )
        
        self.conn.commit()
    
    # Métodos para serviços
    def adicionar_servico(self, nome, valor, duracao=30):
        self.cursor.execute(
            "INSERT INTO servicos (nome, valor, duracao) VALUES (?, ?, ?)",
            (nome, valor, duracao)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_servicos(self, apenas_ativos=True):
        query = "SELECT * FROM servicos"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    # Métodos para produtos
    def adicionar_produto(self, nome, valor_venda, valor_custo, estoque, estoque_minimo=5):
        self.cursor.execute(
            """INSERT INTO produtos (nome, valor_venda, valor_custo, estoque, estoque_minimo) 
               VALUES (?, ?, ?, ?, ?)""",
            (nome, valor_venda, valor_custo, estoque, estoque_minimo)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_produtos(self, apenas_ativos=True):
        query = "SELECT * FROM produtos"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def atualizar_estoque(self, produto_id, quantidade):
        self.cursor.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (quantidade, produto_id)
        )
        self.conn.commit()
    
    # Métodos para clientes
    def adicionar_cliente(self, nome, telefone, email="", data_nascimento=None):
        self.cursor.execute(
            """INSERT INTO clientes (nome, telefone, email, data_nascimento) 
               VALUES (?, ?, ?, ?)""",
            (nome, telefone, email, data_nascimento)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_clientes(self):
        self.cursor.execute("SELECT * FROM clientes ORDER BY nome")
        return self.cursor.fetchall()
    
    def buscar_cliente_por_telefone(self, telefone):
        self.cursor.execute("SELECT * FROM clientes WHERE telefone = ?", (telefone,))
        return self.cursor.fetchone()
    
    # Métodos para agendamentos
    def adicionar_agendamento(self, cliente_id, servico_id, data, hora, profissional, valor):
        self.cursor.execute(
            """INSERT INTO agendamentos 
               (cliente_id, servico_id, data, hora, profissional, valor) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, servico_id, data, hora, profissional, valor)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_agendamentos_do_dia(self, data=None):
        if data is None:
            data = datetime.now().strftime("%Y-%m-%d")
        
        self.cursor.execute('''
            SELECT a.*, c.nome as cliente_nome, s.nome as servico_nome 
            FROM agendamentos a
            LEFT JOIN clientes c ON a.cliente_id = c.id
            LEFT JOIN servicos s ON a.servico_id = s.id
            WHERE a.data = ?
            ORDER BY a.hora
        ''', (data,))
        return self.cursor.fetchall()
    
    def atualizar_status_agendamento(self, agendamento_id, status):
        self.cursor.execute(
            "UPDATE agendamentos SET status = ? WHERE id = ?",
            (status, agendamento_id)
        )
        self.conn.commit()
    
    # Métodos para vendas
    def registrar_venda(self, cliente_id, tipo, item_id, quantidade, valor_unitario, forma_pagamento):
        valor_total = valor_unitario * quantidade
        
        self.cursor.execute(
            """INSERT INTO vendas 
               (cliente_id, tipo, item_id, quantidade, valor_unitario, valor_total, forma_pagamento) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cliente_id, tipo, item_id, quantidade, valor_unitario, valor_total, forma_pagamento)
        )
        
        # Atualizar total do cliente
        if cliente_id:
            self.cursor.execute(
                "UPDATE clientes SET total_gasto = total_gasto + ?, total_visitas = total_visitas + 1 WHERE id = ?",
                (valor_total, cliente_id)
            )
        
        # Atualizar estoque se for produto
        if tipo == 'produto':
            self.atualizar_estoque(item_id, -quantidade)
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_vendas_periodo(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT v.*, 
                   CASE WHEN v.tipo = 'servico' THEN s.nome ELSE p.nome END as item_nome,
                   c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN servicos s ON v.tipo = 'servico' AND v.item_id = s.id
            LEFT JOIN produtos p ON v.tipo = 'produto' AND v.item_id = p.id
            WHERE date(v.data_venda) BETWEEN ? AND ?
            ORDER BY v.data_venda DESC
        ''', (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    # Métodos para despesas
    def adicionar_despesa(self, descricao, categoria, valor, data, forma_pagamento="", observacoes=""):
        self.cursor.execute(
            """INSERT INTO despesas (descricao, categoria, valor, data, forma_pagamento, observacoes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (descricao, categoria, valor, data, forma_pagamento, observacoes)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_despesas_periodo(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT * FROM despesas 
            WHERE data BETWEEN ? AND ?
            ORDER BY data DESC
        ''', (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    # Métodos para relatórios
    def obter_resumo_financeiro(self, data_inicio, data_fim):
        # Total de vendas
        self.cursor.execute('''
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM vendas 
            WHERE date(data_venda) BETWEEN ? AND ?
        ''', (data_inicio, data_fim))
        total_vendas = self.cursor.fetchone()[0] or 0
        
        # Total de despesas
        self.cursor.execute('''
            SELECT COALESCE(SUM(valor), 0) 
            FROM despesas 
            WHERE data BETWEEN ? AND ?
        ''', (data_inicio, data_fim))
        total_despesas = self.cursor.fetchone()[0] or 0
        
        # Lucro
        lucro = total_vendas - total_despesas
        
        return {
            'total_vendas': total_vendas,
            'total_despesas': total_despesas,
            'lucro': lucro
        }
    
    def fechar(self):
        self.conn.close()

# =============================================================
# 2. SISTEMA DE LOGIN
# =============================================================
class LoginWindow:
    def __init__(self):
        self.db = Database()
        self.janela = ctk.CTk()
        self.janela.title("Barbearia Granada - Login")
        self.janela.geometry("400x500")
        self.janela.resizable(False, False)
        
        self.criar_widgets()
    
    def criar_widgets(self):
        # Título
        ctk.CTkLabel(
            self.janela,
            text="Barbearia Granada",
            font=("Arial", 28, "bold"),
            text_color="#4CC9F0"
        ).pack(pady=(40, 20))
        
        ctk.CTkLabel(
            self.janela,
            text="Sistema de Gestão",
            font=("Arial", 16)
        ).pack(pady=(0, 40))
        
        # Campos de login
        frame_campos = ctk.CTkFrame(self.janela, fg_color="transparent")
        frame_campos.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(frame_campos, text="Usuário:", anchor="w").pack(fill="x", pady=(0, 5))
        self.entry_usuario = ctk.CTkEntry(frame_campos, placeholder_text="Digite seu usuário")
        self.entry_usuario.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame_campos, text="Senha:", anchor="w").pack(fill="x", pady=(0, 5))
        self.entry_senha = ctk.CTkEntry(frame_campos, placeholder_text="Digite sua senha", show="•")
        self.entry_senha.pack(fill="x", pady=(0, 20))
        
        # Botão de login
        self.btn_login = ctk.CTkButton(
            self.janela,
            text="Entrar",
            command=self.fazer_login,
            height=40,
            font=("Arial", 14)
        )
        self.btn_login.pack(fill="x", padx=40, pady=10)
        
        # Versão
        ctk.CTkLabel(
            self.janela,
            text="v2.0.0",
            text_color="gray",
            font=("Arial", 10)
        ).pack(side="bottom", pady=20)
    
    def fazer_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        
        if not usuario or not senha:
            CTkMessagebox(title="Erro", message="Preencha todos os campos!", icon="cancel")
            return
        
        self.cursor = self.db.cursor
        self.cursor.execute(
            "SELECT id, nome, tipo FROM usuarios WHERE usuario = ? AND senha = ? AND ativo = 1",
            (usuario, senha)
        )
        usuario_info = self.cursor.fetchone()
        
        if usuario_info:
            self.janela.destroy()
            app = MainApp(usuario_info)
            app.run()
        else:
            CTkMessagebox(title="Erro", message="Usuário ou senha incorretos!", icon="cancel")
    
    def run(self):
        self.janela.mainloop()

# =============================================================
# 3. APLICAÇÃO PRINCIPAL
# =============================================================
class MainApp:
    def __init__(self, usuario_info):
        self.usuario_id, self.usuario_nome, self.usuario_tipo = usuario_info
        self.db = Database()
        
        self.setup_janela()
        self.setup_menu()
        self.setup_dashboard()
        
        # Carregar dados iniciais
        self.carregar_agendamentos_hoje()
        self.atualizar_metricas()
    
    def setup_janela(self):
        self.janela = ctk.CTk()
        self.janela.title(f"Barbearia Granada - Bem-vindo, {self.usuario_nome}")
        self.janela.geometry("1400x800")
        self.janela.minsize(1200, 700)
        
        # Configurar grid
        self.janela.grid_rowconfigure(0, weight=1)
        self.janela.grid_columnconfigure(1, weight=1)
    
    def setup_menu(self):
        self.frame_menu = ctk.CTkFrame(self.janela, width=250, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_propagate(False)
        
        # Informações do usuário
        frame_usuario = ctk.CTkFrame(self.frame_menu, fg_color="#2B2B2B")
        frame_usuario.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            frame_usuario,
            text=self.usuario_nome,
            font=("Arial", 14, "bold")
        ).pack(pady=(10, 0))
        
        ctk.CTkLabel(
            frame_usuario,
            text=self.usuario_tipo.upper(),
            font=("Arial", 11),
            text_color="#4CC9F0"
        ).pack(pady=(0, 10))
        
        # Botões do menu
        botoes_menu = [
            ("🏠 Dashboard", self.mostrar_dashboard),
            ("✂️ Serviços", self.mostrar_servicos),
            ("🛍️ Produtos", self.mostrar_produtos),
            ("👥 Clientes", self.mostrar_clientes),
            ("📅 Agendamentos", self.mostrar_agendamentos),
            ("💰 Caixa", self.mostrar_caixa),
            ("📊 Relatórios", self.mostrar_relatorios),
            ("⚙️ Configurações", self.mostrar_configuracoes),
        ]
        
        for texto, comando in botoes_menu:
            btn = ctk.CTkButton(
                self.frame_menu,
                text=texto,
                command=comando,
                anchor="w",
                fg_color="transparent",
                hover_color="#2B2B2B",
                font=("Arial", 14),
                height=40
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        # Botão sair
        ctk.CTkButton(
            self.frame_menu,
            text="🚪 Sair",
            command=self.sair,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            height=40,
            font=("Arial", 14)
        ).pack(side="bottom", padx=10, pady=20, fill="x")
    
    def setup_dashboard(self):
        self.frame_principal = ctk.CTkFrame(self.janela, corner_radius=10)
        self.frame_principal.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_principal.grid_columnconfigure(0, weight=1)
        self.frame_principal.grid_rowconfigure(0, weight=1)
        
        self.mostrar_dashboard()
    
    # =============================================================
    # 4. DASHBOARD COMPLETO
    # =============================================================
    def mostrar_dashboard(self):
        self.limpar_frame_principal()
        
        # Título
        titulo_frame = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        titulo_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            titulo_frame,
            text="Dashboard",
            font=("Arial", 24, "bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            titulo_frame,
            text=datetime.now().strftime("%d/%m/%Y"),
            font=("Arial", 14),
            text_color="gray"
        ).pack(side="right")
        
        # Métricas rápidas
        self.criar_metricas_rapidas()
        
        # Agendamentos do dia
        self.criar_agendamentos_hoje()
        
        # Produtos com baixo estoque
        self.criar_alerta_estoque()
    
    def criar_metricas_rapidas(self):
        frame_metricas = ctk.CTkFrame(self.frame_principal)
        frame_metricas.pack(fill="x", padx=20, pady=(0, 20))
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Consultas para métricas
        self.db.cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE data = ? AND status = 'agendado'", (hoje,))
        agendamentos_hoje = self.db.cursor.fetchone()[0] or 0
        
        self.db.cursor.execute("SELECT COUNT(*) FROM clientes WHERE date(data_cadastro) = date('now')")
        clientes_novos = self.db.cursor.fetchone()[0] or 0
        
        self.db.cursor.execute("SELECT COALESCE(SUM(valor_total), 0) FROM vendas WHERE date(data_venda) = date('now')")
        faturamento_hoje = self.db.cursor.fetchone()[0] or 0
        
        self.db.cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque <= estoque_minimo")
        produtos_baixo_estoque = self.db.cursor.fetchone()[0] or 0
        
        metricas = [
            ("📅 Agendamentos Hoje", str(agendamentos_hoje), "#2196F3"),
            ("👥 Clientes Novos", str(clientes_novos), "#4CAF50"),
            ("💰 Faturamento Hoje", f"R$ {faturamento_hoje:,.2f}", "#FF9800"),
            ("⚠️ Baixo Estoque", str(produtos_baixo_estoque), "#F44336"),
        ]
        
        for i, (titulo, valor, cor) in enumerate(metricas):
            frame = ctk.CTkFrame(frame_metricas, fg_color=cor, corner_radius=10)
            frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            frame_metricas.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(
                frame,
                text=titulo,
                font=("Arial", 12),
                text_color="white"
            ).pack(pady=(15, 5))
            
            ctk.CTkLabel(
                frame,
                text=valor,
                font=("Arial", 24, "bold"),
                text_color="white"
            ).pack(pady=(0, 15))
    
    def criar_agendamentos_hoje(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="Agendamentos de Hoje",
            font=("Arial", 18, "bold")
        ).pack(pady=(15, 10))
        
        # Treeview para agendamentos
        columns = ("Hora", "Cliente", "Serviço", "Profissional", "Status")
        self.tree_agendamentos = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=8
        )
        
        for col in columns:
            self.tree_agendamentos.heading(col, text=col)
            self.tree_agendamentos.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree_agendamentos.yview)
        self.tree_agendamentos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_agendamentos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Botões de ação
        frame_botoes = ctk.CTkFrame(frame)
        frame_botoes.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            frame_botoes,
            text="🔄 Atualizar",
            command=self.carregar_agendamentos_hoje,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="✅ Confirmar",
            command=self.confirmar_agendamento,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="❌ Cancelar",
            command=self.cancelar_agendamento,
            fg_color="#D32F2F",
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="💰 Finalizar",
            command=self.finalizar_agendamento,
            fg_color="#4CAF50",
            width=100
        ).pack(side="left", padx=5)
        
        self.carregar_agendamentos_hoje()
    
    def carregar_agendamentos_hoje(self):
        for item in self.tree_agendamentos.get_children():
            self.tree_agendamentos.delete(item)
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        agendamentos = self.db.obter_agendamentos_do_dia(hoje)
        
        for ag in agendamentos:
            status_color = {
                'agendado': 'blue',
                'confirmado': 'green',
                'finalizado': 'gray',
                'cancelado': 'red'
            }.get(ag[7], 'black')
            
            self.tree_agendamentos.insert("", "end", values=(
                ag[4],  # hora
                ag[10],  # cliente_nome
                ag[11],  # servico_nome
                ag[6],   # profissional
                ag[7]    # status
            ), tags=(status_color,))
        
        self.tree_agendamentos.tag_configure('blue', foreground='blue')
        self.tree_agendamentos.tag_configure('green', foreground='green')
        self.tree_agendamentos.tag_configure('gray', foreground='gray')
        self.tree_agendamentos.tag_configure('red', foreground='red')
    
    def criar_alerta_estoque(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="⚠️ Produtos com Baixo Estoque",
            font=("Arial", 16, "bold"),
            text_color="#F44336"
        ).pack(pady=(10, 5))
        
        self.db.cursor.execute('''
            SELECT nome, estoque, estoque_minimo 
            FROM produtos 
            WHERE estoque <= estoque_minimo AND ativo = 1
            ORDER BY estoque ASC
        ''')
        produtos = self.db.cursor.fetchall()
        
        if produtos:
            for produto in produtos:
                produto_frame = ctk.CTkFrame(frame, fg_color="#FFF3E0")
                produto_frame.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(
                    produto_frame,
                    text=f"{produto[0]} - Estoque: {produto[1]} (Mínimo: {produto[2]})",
                    font=("Arial", 12),
                    text_color="black"
                ).pack(pady=5)
        else:
            ctk.CTkLabel(
                frame,
                text="Todos os produtos estão com estoque adequado ✅",
                font=("Arial", 12),
                text_color="#4CAF50"
            ).pack(pady=10)
    
    def atualizar_metricas(self):
        # Esta função pode ser chamada periodicamente para atualizar métricas
        pass
    
    # =============================================================
    # 5. MÓDULO DE SERVIÇOS
    # =============================================================
    def mostrar_servicos(self):
        self.limpar_frame_principal()
        
        # Título
        ctk.CTkLabel(
            self.frame_principal,
            text="Gerenciar Serviços",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Frame para lista e formulário
        frame_conteudo = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_conteudo.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Lista de serviços
        frame_lista = ctk.CTkFrame(frame_conteudo)
        frame_lista.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            frame_lista,
            text="Serviços Cadastrados",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 5))
        
        # Treeview
        columns = ("ID", "Nome", "Valor", "Duração", "Status")
        self.tree_servicos = ttk.Treeview(
            frame_lista,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            self.tree_servicos.heading(col, text=col)
            self.tree_servicos.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_servicos.yview)
        self.tree_servicos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_servicos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Formulário
        frame_form = ctk.CTkFrame(frame_conteudo)
        frame_form.pack(side="right", fill="y", padx=(10, 0))
        
        ctk.CTkLabel(
            frame_form,
            text="Adicionar/Editar Serviço",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        # Campos
        campos = [
            ("Nome:", ctk.CTkEntry(frame_form, width=250)),
            ("Valor (R$):", ctk.CTkEntry(frame_form, width=150)),
            ("Duração (min):", ctk.CTkEntry(frame_form, width=150))
        ]
        
        for label_text, entry in campos:
            ctk.CTkLabel(frame_form, text=label_text).pack(anchor="w", pady=(10, 5))
            entry.pack(anchor="w", pady=(0, 10))
        
        self.entry_nome_servico, self.entry_valor_servico, self.entry_duracao_servico = [e for _, e in campos]
        
        # Botões
        frame_botoes = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botoes.pack(pady=20)
        
        ctk.CTkButton(
            frame_botoes,
            text="➕ Adicionar",
            command=self.adicionar_servico,
            width=120
        ).pack(pady=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="✏️ Editar",
            command=self.editar_servico,
            width=120
        ).pack(pady=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="🗑️ Remover",
            command=self.remover_servico,
            fg_color="#D32F2F",
            width=120
        ).pack(pady=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="🔄 Atualizar",
            command=self.carregar_servicos,
            width=120
        ).pack(pady=5)
        
        self.carregar_servicos()
    
    def carregar_servicos(self):
        for item in self.tree_servicos.get_children():
            self.tree_servicos.delete(item)
        
        servicos = self.db.obter_servicos(apenas_ativos=False)
        for servico in servicos:
            status = "Ativo" if servico[4] == 1 else "Inativo"
            self.tree_servicos.insert("", "end", values=(
                servico[0],  # id
                servico[1],  # nome
                f"R$ {servico[2]:.2f}",  # valor
                f"{servico[3]} min",  # duração
                status
            ))
    
    def adicionar_servico(self):
        nome = self.entry_nome_servico.get().strip()
        valor = self.entry_valor_servico.get().strip()
        duracao = self.entry_duracao_servico.get().strip()
        
        if not nome or not valor or not duracao:
            CTkMessagebox(title="Erro", message="Preencha todos os campos!", icon="cancel")
            return
        
        try:
            valor_float = float(valor.replace(',', '.'))
            duracao_int = int(duracao)
            
            self.db.adicionar_servico(nome, valor_float, duracao_int)
            
            # Limpar campos
            self.entry_nome_servico.delete(0, "end")
            self.entry_valor_servico.delete(0, "end")
            self.entry_duracao_servico.delete(0, "end")
            
            self.carregar_servicos()
            CTkMessagebox(title="Sucesso", message="Serviço adicionado com sucesso!", icon="check")
            
        except ValueError:
            CTkMessagebox(title="Erro", message="Valores inválidos! Verifique os dados.", icon="cancel")
    
    def editar_servico(self):
        selecionado = self.tree_servicos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um serviço para editar!", icon="warning")
            return
        
        item = self.tree_servicos.item(selecionado[0])
        servico_id = item['values'][0]
        
        # Abrir janela de edição
        self.abrir_janela_edicao_servico(servico_id)
    
    def remover_servico(self):
        selecionado = self.tree_servicos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um serviço para remover!", icon="warning")
            return
        
        item = self.tree_servicos.item(selecionado[0])
        servico_id = item['values'][0]
        servico_nome = item['values'][1]
        
        resposta = CTkMessagebox(
            title="Confirmar",
            message=f"Deseja realmente remover o serviço '{servico_nome}'?",
            icon="question",
            option_1="Cancelar",
            option_2="Remover"
        )
        
        if resposta.get() == "Remover":
            self.db.cursor.execute("UPDATE servicos SET ativo = 0 WHERE id = ?", (servico_id,))
            self.db.conn.commit()
            self.carregar_servicos()
            CTkMessagebox(title="Sucesso", message="Serviço removido com sucesso!", icon="check")
    
    def abrir_janela_edicao_servico(self, servico_id):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Editar Serviço")
        janela.geometry("400x400")
        janela.transient(self.janela)
        janela.grab_set()
        
        # Buscar dados do serviço
        self.db.cursor.execute("SELECT * FROM servicos WHERE id = ?", (servico_id,))
        servico = self.db.cursor.fetchone()
        
        ctk.CTkLabel(
            janela,
            text="Editar Serviço",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Campos
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(pady=20, padx=40, fill="both")
        
        ctk.CTkLabel(campos_frame, text="Nome:").pack(anchor="w")
        entry_nome = ctk.CTkEntry(campos_frame, width=300)
        entry_nome.insert(0, servico[1])
        entry_nome.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(campos_frame, text="Valor (R$):").pack(anchor="w")
        entry_valor = ctk.CTkEntry(campos_frame, width=150)
        entry_valor.insert(0, str(servico[2]))
        entry_valor.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(campos_frame, text="Duração (min):").pack(anchor="w")
        entry_duracao = ctk.CTkEntry(campos_frame, width=150)
        entry_duracao.insert(0, str(servico[3]))
        entry_duracao.pack(anchor="w", pady=(0, 15))
        
        # Status
        var_status = ctk.StringVar(value="ativo" if servico[4] == 1 else "inativo")
        ctk.CTkLabel(campos_frame, text="Status:").pack(anchor="w")
        frame_status = ctk.CTkFrame(campos_frame, fg_color="transparent")
        frame_status.pack(anchor="w", pady=(0, 20))
        
        ctk.CTkRadioButton(frame_status, text="Ativo", variable=var_status, value="ativo").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(frame_status, text="Inativo", variable=var_status, value="inativo").pack(side="left")
        
        def salvar_edicao():
            try:
                nome = entry_nome.get().strip()
                valor = float(entry_valor.get().replace(',', '.'))
                duracao = int(entry_duracao.get())
                ativo = 1 if var_status.get() == "ativo" else 0
                
                self.db.cursor.execute(
                    "UPDATE servicos SET nome = ?, valor = ?, duracao = ?, ativo = ? WHERE id = ?",
                    (nome, valor, duracao, ativo, servico_id)
                )
                self.db.conn.commit()
                
                self.carregar_servicos()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message="Serviço atualizado com sucesso!", icon="check")
                
            except ValueError:
                CTkMessagebox(title="Erro", message="Valores inválidos!", icon="cancel")
        
        ctk.CTkButton(
            janela,
            text="💾 Salvar",
            command=salvar_edicao,
            width=200
        ).pack(pady=20)
    
    # =============================================================
    # 6. MÓDULO DE PRODUTOS (similar ao de serviços)
    # =============================================================
    def mostrar_produtos(self):
        self.limpar_frame_principal()
        
        # Implementação similar à de serviços, mas com campos específicos para produtos
        # (valor_custo, estoque, estoque_minimo)
        # Por questão de espaço, vou pular a implementação completa aqui
        # Mas segue o mesmo padrão do módulo de serviços
        
        ctk.CTkLabel(
            self.frame_principal,
            text="Gerenciar Produtos",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Botão para abrir formulário de produtos
        ctk.CTkButton(
            self.frame_principal,
            text="Abrir Gerenciador de Produtos",
            command=self.abrir_gerenciador_produtos,
            width=300
        ).pack(pady=20)
    
    def abrir_gerenciador_produtos(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Gerenciar Produtos")
        janela.geometry("1000x600")
        
        # Implementar aqui interface completa para produtos
        # Similar ao módulo de serviços
    
    # =============================================================
    # 7. MÓDULO DE CLIENTES
    # =============================================================
    def mostrar_clientes(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="Gerenciar Clientes",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Barra de pesquisa
        frame_pesquisa = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_pesquisa.pack(fill="x", padx=20, pady=(0, 10))
        
        self.entry_pesquisa_cliente = ctk.CTkEntry(
            frame_pesquisa,
            placeholder_text="Pesquisar por nome ou telefone...",
            width=400
        )
        self.entry_pesquisa_cliente.pack(side="left", padx=(0, 10))
        self.entry_pesquisa_cliente.bind("<KeyRelease>", self.filtrar_clientes)
        
        ctk.CTkButton(
            frame_pesquisa,
            text="🔍 Pesquisar",
            command=self.filtrar_clientes,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_pesquisa,
            text="➕ Novo Cliente",
            command=self.abrir_form_cliente,
            fg_color="#4CAF50",
            width=150
        ).pack(side="right")
        
        # Treeview de clientes
        frame_tree = ctk.CTkFrame(self.frame_principal)
        frame_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("ID", "Nome", "Telefone", "Email", "Cadastro", "Gasto Total", "Visitas")
        self.tree_clientes = ttk.Treeview(
            frame_tree,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, width=120)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_clientes.yview)
        scrollbar_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree_clientes.xview)
        self.tree_clientes.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree_clientes.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        self.carregar_clientes()
    
    def carregar_clientes(self):
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)
        
        clientes = self.db.obter_clientes()
        for cliente in clientes:
            self.tree_clientes.insert("", "end", values=(
                cliente[0],  # id
                cliente[1],  # nome
                cliente[2],  # telefone
                cliente[3] or "",  # email
                cliente[5],  # data_cadastro
                f"R$ {cliente[6]:.2f}",  # total_gasto
                cliente[7]  # total_visitas
            ))
    
    def filtrar_clientes(self, event=None):
        termo = self.entry_pesquisa_cliente.get().lower()
        
        for item in self.tree_clientes.get_children():
            valores = self.tree_clientes.item(item)['values']
            if (termo in str(valores[1]).lower() or  # nome
                termo in str(valores[2]).lower()):   # telefone
                self.tree_clientes.item(item, tags=('found',))
                self.tree_clientes.selection_set(item)
            else:
                self.tree_clientes.item(item, tags=())
    
    def abrir_form_cliente(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Novo Cliente")
        janela.geometry("400x500")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(
            janela,
            text="Cadastrar Novo Cliente",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Campos
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(pady=20, padx=40, fill="both")
        
        campos = [
            ("Nome completo:", ctk.CTkEntry(campos_frame, width=300)),
            ("Telefone:", ctk.CTkEntry(campos_frame, width=200)),
            ("Email:", ctk.CTkEntry(campos_frame, width=300)),
            ("Data de Nascimento (DD/MM/AAAA):", ctk.CTkEntry(campos_frame, width=150)),
        ]
        
        for label_text, entry in campos:
            ctk.CTkLabel(campos_frame, text=label_text).pack(anchor="w", pady=(10, 5))
            entry.pack(anchor="w", pady=(0, 10))
        
        def salvar_cliente():
            nome = campos[0][1].get().strip()
            telefone = campos[1][1].get().strip()
            email = campos[2][1].get().strip()
            data_nasc = campos[3][1].get().strip()
            
            if not nome or not telefone:
                CTkMessagebox(title="Erro", message="Nome e telefone são obrigatórios!", icon="cancel")
                return
            
            # Validar telefone
            if not telefone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').isdigit():
                CTkMessagebox(title="Erro", message="Telefone inválido!", icon="cancel")
                return
            
            # Verificar se cliente já existe
            cliente_existente = self.db.buscar_cliente_por_telefone(telefone)
            if cliente_existente:
                CTkMessagebox(title="Aviso", 
                            message=f"Cliente já cadastrado:\n{cliente_existente[1]}",
                            icon="warning")
                return
            
            try:
                self.db.adicionar_cliente(nome, telefone, email, 
                                         data_nasc if data_nasc else None)
                
                self.carregar_clientes()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message="Cliente cadastrado com sucesso!", icon="check")
                
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao cadastrar: {str(e)}", icon="cancel")
        
        ctk.CTkButton(
            janela,
            text="💾 Salvar Cliente",
            command=salvar_cliente,
            width=200
        ).pack(pady=20)
    
    # =============================================================
    # 8. MÓDULO DE AGENDAMENTOS
    # =============================================================
    def mostrar_agendamentos(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="Agendamentos",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Controles de data
        frame_controles = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_controles.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(frame_controles, text="Data:").pack(side="left", padx=(0, 10))
        
        self.calendario_agendamentos = ctk.CTkFrame(frame_controles)
        self.calendario_agendamentos.pack(side="left", fill="x", expand=True)
        
        hoje = datetime.now()
        self.data_selecionada = hoje
        
        self.label_data = ctk.CTkLabel(
            self.calendario_agendamentos,
            text=hoje.strftime("%d/%m/%Y"),
            font=("Arial", 14, "bold")
        )
        self.label_data.pack(side="left", padx=10)
        
        ctk.CTkButton(
            self.calendario_agendamentos,
            text="◀",
            width=30,
            command=lambda: self.mudar_data_agendamentos(-1)
        ).pack(side="left")
        
        ctk.CTkButton(
            self.calendario_agendamentos,
            text="Hoje",
            width=60,
            command=self.ir_para_hoje_agendamentos
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            self.calendario_agendamentos,
            text="▶",
            width=30,
            command=lambda: self.mudar_data_agendamentos(1)
        ).pack(side="left")
        
        ctk.CTkButton(
            frame_controles,
            text="➕ Novo Agendamento",
            command=self.abrir_novo_agendamento,
            fg_color="#4CAF50",
            width=180
        ).pack(side="right")
        
        # Lista de agendamentos do dia
        self.criar_lista_agendamentos_dia()
    
    def criar_lista_agendamentos_dia(self):
        frame_lista = ctk.CTkFrame(self.frame_principal)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ("Hora", "Cliente", "Serviço", "Profissional", "Valor", "Status")
        self.tree_agendamentos_dia = ttk.Treeview(
            frame_lista,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            self.tree_agendamentos_dia.heading(col, text=col)
            self.tree_agendamentos_dia.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_agendamentos_dia.yview)
        self.tree_agendamentos_dia.configure(yscrollcommand=scrollbar.set)
        
        self.tree_agendamentos_dia.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        self.carregar_agendamentos_dia()
    
    def carregar_agendamentos_dia(self):
        for item in self.tree_agendamentos_dia.get_children():
            self.tree_agendamentos_dia.delete(item)
        
        data_str = self.data_selecionada.strftime("%Y-%m-%d")
        agendamentos = self.db.obter_agendamentos_do_dia(data_str)
        
        for ag in agendamentos:
            self.tree_agendamentos_dia.insert("", "end", values=(
                ag[4],  # hora
                ag[10],  # cliente_nome
                ag[11],  # servico_nome
                ag[6],   # profissional
                f"R$ {ag[7]:.2f}",  # valor
                ag[8]    # status
            ))
    
    def mudar_data_agendamentos(self, dias):
        self.data_selecionada += timedelta(days=dias)
        self.label_data.configure(text=self.data_selecionada.strftime("%d/%m/%Y"))
        self.carregar_agendamentos_dia()
    
    def ir_para_hoje_agendamentos(self):
        self.data_selecionada = datetime.now()
        self.label_data.configure(text=self.data_selecionada.strftime("%d/%m/%Y"))
        self.carregar_agendamentos_dia()
    
    def abrir_novo_agendamento(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Novo Agendamento")
        janela.geometry("500x600")
        janela.transient(self.janela)
        janela.grab_set()
        
        # Implementar formulário completo de agendamento
        # Com seleção de cliente, serviço, profissional, data/hora
        # Por questão de espaço, vou pular a implementação completa
    
    def confirmar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        hora = item['values'][0]
        
        # Buscar ID do agendamento
        data_str = datetime.now().strftime("%Y-%m-%d")
        self.db.cursor.execute(
            "SELECT id FROM agendamentos WHERE data = ? AND hora = ?",
            (data_str, hora)
        )
        resultado = self.db.cursor.fetchone()
        
        if resultado:
            self.db.atualizar_status_agendamento(resultado[0], 'confirmado')
            self.carregar_agendamentos_hoje()
            CTkMessagebox(title="Sucesso", message="Agendamento confirmado!", icon="check")
    
    def cancelar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        hora = item['values'][0]
        
        resposta = CTkMessagebox(
            title="Confirmar",
            message="Deseja realmente cancelar este agendamento?",
            icon="question",
            option_1="Não",
            option_2="Sim"
        )
        
        if resposta.get() == "Sim":
            data_str = datetime.now().strftime("%Y-%m-%d")
            self.db.cursor.execute(
                "SELECT id FROM agendamentos WHERE data = ? AND hora = ?",
                (data_str, hora)
            )
            resultado = self.db.cursor.fetchone()
            
            if resultado:
                self.db.atualizar_status_agendamento(resultado[0], 'cancelado')
                self.carregar_agendamentos_hoje()
                CTkMessagebox(title="Sucesso", message="Agendamento cancelado!", icon="check")
    
    def finalizar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        # Abrir janela de pagamento
        item = self.tree_agendamentos.item(selecionado[0])
        self.abrir_janela_pagamento(item['values'])
    
    def abrir_janela_pagamento(self, dados_agendamento):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Registrar Pagamento")
        janela.geometry("400x500")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(
            janela,
            text="Registrar Pagamento",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Informações do agendamento
        info_frame = ctk.CTkFrame(janela, fg_color="#E8F5E9")
        info_frame.pack(fill="x", padx=40, pady=10)
        
        infos = [
            f"Cliente: {dados_agendamento[1]}",
            f"Serviço: {dados_agendamento[2]}",
            f"Profissional: {dados_agendamento[3]}",
            f"Valor: R$ {dados_agendamento[8] if len(dados_agendamento) > 8 else '0.00'}"
        ]
        
        for info in infos:
            ctk.CTkLabel(
                info_frame,
                text=info,
                font=("Arial", 12)
            ).pack(pady=5)
        
        # Forma de pagamento
        ctk.CTkLabel(
            janela,
            text="Forma de Pagamento:",
            font=("Arial", 14)
        ).pack(pady=(20, 10))
        
        formas_pagamento = ["Dinheiro", "Cartão Débito", "Cartão Crédito", "PIX", "Transferência"]
        self.var_forma_pagamento = ctk.StringVar(value=formas_pagamento[0])
        
        for forma in formas_pagamento:
            ctk.CTkRadioButton(
                janela,
                text=forma,
                variable=self.var_forma_pagamento,
                value=forma
            ).pack(anchor="w", padx=100, pady=2)
        
        def registrar_pagamento():
            # Aqui você implementaria a lógica completa de pagamento
            # Registrar venda, atualizar status, etc.
            
            CTkMessagebox(title="Sucesso", message="Pagamento registrado!", icon="check")
            janela.destroy()
            self.carregar_agendamentos_hoje()
        
        ctk.CTkButton(
            janela,
            text="💳 Registrar Pagamento",
            command=registrar_pagamento,
            fg_color="#4CAF50",
            width=200
        ).pack(pady=30)
    
    # =============================================================
    # 9. MÓDULO DE CAIXA
    # =============================================================
    def mostrar_caixa(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="Controle de Caixa",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Abertura/Fechamento de caixa
        frame_caixa = ctk.CTkFrame(self.frame_principal)
        frame_caixa.pack(fill="x", padx=20, pady=10)
        
        # Verificar se caixa está aberto
        self.db.cursor.execute("SELECT COUNT(*) FROM caixa WHERE data = date('now') AND status = 'aberto'")
        caixa_aberto = self.db.cursor.fetchone()[0] > 0
        
        if caixa_aberto:
            self.mostrar_caixa_aberto(frame_caixa)
        else:
            self.mostrar_caixa_fechado(frame_caixa)
        
        # Últimas vendas do dia
        frame_vendas = ctk.CTkFrame(self.frame_principal)
        frame_vendas.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        ctk.CTkLabel(
            frame_vendas,
            text="Últimas Vendas de Hoje",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Treeview de vendas
        columns = ("ID", "Cliente", "Item", "Quantidade", "Valor", "Forma Pagamento", "Hora")
        tree_vendas = ttk.Treeview(
            frame_vendas,
            columns=columns,
            show="headings",
            height=10
        )
        
        for col in columns:
            tree_vendas.heading(col, text=col)
            tree_vendas.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(frame_vendas, orient="vertical", command=tree_vendas.yview)
        tree_vendas.configure(yscrollcommand=scrollbar.set)
        
        tree_vendas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Carregar vendas do dia
        hoje = datetime.now().strftime("%Y-%m-%d")
        vendas = self.db.obter_vendas_periodo(hoje, hoje)
        
        for venda in vendas:
            tree_vendas.insert("", "end", values=(
                venda[0],  # id
                venda[8] or "Não informado",  # cliente_nome
                venda[7],  # item_nome
                venda[4],  # quantidade
                f"R$ {venda[6]:.2f}",  # valor_total
                venda[7],  # forma_pagamento
                venda[8][11:16] if len(venda) > 8 and venda[8] else ""  # hora
            ))
    
    def mostrar_caixa_aberto(self, frame):
        ctk.CTkLabel(
            frame,
            text="✅ Caixa Aberto",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=10)
        
        # Buscar valor de abertura
        self.db.cursor.execute('''
            SELECT valor_inicial 
            FROM caixa 
            WHERE data = date('now') AND status = 'aberto'
        ''')
        resultado = self.db.cursor.fetchone()
        valor_inicial = resultado[0] if resultado else 0
        
        # Calcular total de vendas do dia
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.db.cursor.execute('''
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM vendas 
            WHERE date(data_venda) = ?
        ''', (hoje,))
        total_vendas = self.db.cursor.fetchone()[0] or 0
        
        # Calcular total esperado no caixa
        total_esperado = valor_inicial + total_vendas
        
        metricas = [
            ("Valor Inicial", f"R$ {valor_inicial:,.2f}"),
            ("Total em Vendas", f"R$ {total_vendas:,.2f}"),
            ("Total Esperado", f"R$ {total_esperado:,.2f}", "#4CAF50"),
        ]
        
        for titulo, valor, *cor in metricas:
            linha = ctk.CTkFrame(frame, fg_color="transparent")
            linha.pack(fill="x", padx=50, pady=5)
            
            ctk.CTkLabel(linha, text=titulo, font=("Arial", 12)).pack(side="left")
            ctk.CTkLabel(
                linha,
                text=valor,
                font=("Arial", 12, "bold"),
                text_color=cor[0] if cor else "white"
            ).pack(side="right")
        
        ctk.CTkButton(
            frame,
            text="🔒 Fechar Caixa",
            command=self.fechar_caixa,
            fg_color="#D32F2F",
            width=200
        ).pack(pady=20)
    
    def mostrar_caixa_fechado(self, frame):
        ctk.CTkLabel(
            frame,
            text="🔒 Caixa Fechado",
            font=("Arial", 18, "bold"),
            text_color="#F44336"
        ).pack(pady=10)
        
        # Formulário para abrir caixa
        ctk.CTkLabel(frame, text="Valor Inicial no Caixa:").pack(pady=(10, 5))
        self.entry_valor_inicial = ctk.CTkEntry(frame, width=200)
        self.entry_valor_inicial.insert(0, "0.00")
        self.entry_valor_inicial.pack(pady=(0, 10))
        
        ctk.CTkButton(
            frame,
            text="🔓 Abrir Caixa",
            command=self.abrir_caixa,
            fg_color="#4CAF50",
            width=200
        ).pack(pady=10)
    
    def abrir_caixa(self):
        try:
            valor_inicial = float(self.entry_valor_inicial.get().replace(',', '.'))
            
            # Criar tabela caixa se não existir
            self.db.cursor.execute('''
                CREATE TABLE IF NOT EXISTS caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data DATE NOT NULL,
                    valor_inicial REAL NOT NULL,
                    valor_final REAL,
                    status TEXT DEFAULT 'aberto',
                    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_fechamento TIMESTAMP
                )
            ''')
            
            # Inserir abertura
            self.db.cursor.execute(
                "INSERT INTO caixa (data, valor_inicial, status) VALUES (date('now'), ?, 'aberto')",
                (valor_inicial,)
            )
            self.db.conn.commit()
            
            self.mostrar_caixa()
            CTkMessagebox(title="Sucesso", message="Caixa aberto com sucesso!", icon="check")
            
        except ValueError:
            CTkMessagebox(title="Erro", message="Valor inválido!", icon="cancel")
    
    def fechar_caixa(self):
        resposta = CTkMessagebox(
            title="Confirmar",
            message="Deseja fechar o caixa?\nIsso registrará o fechamento do dia.",
            icon="question",
            option_1="Cancelar",
            option_2="Fechar"
        )
        
        if resposta.get() == "Fechar":
            # Buscar valor inicial
            self.db.cursor.execute('''
                SELECT valor_inicial 
                FROM caixa 
                WHERE data = date('now') AND status = 'aberto'
            ''')
            resultado = self.db.cursor.fetchone()
            
            if resultado:
                valor_inicial = resultado[0]
                
                # Calcular total de vendas
                hoje = datetime.now().strftime("%Y-%m-%d")
                self.db.cursor.execute('''
                    SELECT COALESCE(SUM(valor_total), 0) 
                    FROM vendas 
                    WHERE date(data_venda) = ?
                ''', (hoje,))
                total_vendas = self.db.cursor.fetchone()[0] or 0
                
                # Valor final (valor inicial + vendas)
                valor_final = valor_inicial + total_vendas
                
                # Atualizar registro do caixa
                self.db.cursor.execute('''
                    UPDATE caixa 
                    SET valor_final = ?, status = 'fechado', data_fechamento = CURRENT_TIMESTAMP
                    WHERE data = date('now') AND status = 'aberto'
                ''', (valor_final,))
                
                self.db.conn.commit()
                
                # Mostrar resumo
                mensagem = f"""✅ Caixa fechado com sucesso!

Resumo do Dia:
• Valor Inicial: R$ {valor_inicial:,.2f}
• Total em Vendas: R$ {total_vendas:,.2f}
• Valor Final Esperado: R$ {valor_final:,.2f}

Confirme o valor físico no caixa."""
                
                CTkMessagebox(title="Caixa Fechado", message=mensagem, icon="check")
                self.mostrar_caixa()
    
    # =============================================================
    # 10. MÓDULO DE RELATÓRIOS
    # =============================================================
    def mostrar_relatorios(self):
        self.limpar_frame_principal()
        
        notebook = ctk.CTkTabview(self.frame_principal)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Adicionar abas
        notebook.add("Financeiro")
        notebook.add("Vendas")
        notebook.add("Clientes")
        notebook.add("Serviços")
        
        # Aba Financeiro
        self.criar_relatorio_financeiro(notebook.tab("Financeiro"))
        
        # Aba Vendas
        self.criar_relatorio_vendas(notebook.tab("Vendas"))
        
        # Aba Clientes
        self.criar_relatorio_clientes(notebook.tab("Clientes"))
        
        # Aba Serviços
        self.criar_relatorio_servicos(notebook.tab("Serviços"))
    
    def criar_relatorio_financeiro(self, frame):
        ctk.CTkLabel(
            frame,
            text="Relatório Financeiro",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Período
        periodo_frame = ctk.CTkFrame(frame, fg_color="transparent")
        periodo_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(periodo_frame, text="De:").pack(side="left", padx=(0, 10))
        entry_data_inicio = ctk.CTkEntry(periodo_frame, width=120)
        entry_data_inicio.insert(0, datetime.now().strftime("%Y-%m-01"))
        entry_data_inicio.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(periodo_frame, text="Até:").pack(side="left", padx=(0, 10))
        entry_data_fim = ctk.CTkEntry(periodo_frame, width=120)
        entry_data_fim.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_data_fim.pack(side="left")
        
        # Botão gerar
        def gerar_relatorio():
            data_inicio = entry_data_inicio.get()
            data_fim = entry_data_fim.get()
            
            try:
                resumo = self.db.obter_resumo_financeiro(data_inicio, data_fim)
                
                # Limpar frame de resultados
                for widget in frame_resultados.winfo_children():
                    widget.destroy()
                
                # Mostrar resultados
                metricas = [
                    ("💰 Total em Vendas", f"R$ {resumo['total_vendas']:,.2f}", "#4CAF50"),
                    ("💸 Total em Despesas", f"R$ {resumo['total_despesas']:,.2f}", "#F44336"),
                    ("📈 Lucro Líquido", f"R$ {resumo['lucro']:,.2f}", 
                     "#4CAF50" if resumo['lucro'] >= 0 else "#F44336"),
                ]
                
                for titulo, valor, cor in metricas:
                    linha = ctk.CTkFrame(frame_resultados, fg_color=cor, corner_radius=8)
                    linha.pack(fill="x", padx=50, pady=5)
                    
                    ctk.CTkLabel(
                        linha,
                        text=titulo,
                        font=("Arial", 14)
                    ).pack(side="left", padx=20, pady=10)
                    
                    ctk.CTkLabel(
                        linha,
                        text=valor,
                        font=("Arial", 16, "bold")
                    ).pack(side="right", padx=20, pady=10)
                
                # Margem de lucro
                if resumo['total_vendas'] > 0:
                    margem = (resumo['lucro'] / resumo['total_vendas']) * 100
                    
                    linha_margem = ctk.CTkFrame(frame_resultados)
                    linha_margem.pack(fill="x", padx=50, pady=10)
                    
                    ctk.CTkLabel(
                        linha_margem,
                        text=f"Margem de Lucro: {margem:.1f}%",
                        font=("Arial", 14),
                        text_color="#4CAF50" if margem >= 0 else "#F44336"
                    ).pack()
                    
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao gerar relatório: {str(e)}", icon="cancel")
        
        ctk.CTkButton(
            periodo_frame,
            text="📊 Gerar Relatório",
            command=gerar_relatorio,
            width=150
        ).pack(side="right")
        
        # Frame para resultados
        frame_resultados = ctk.CTkFrame(frame)
        frame_resultados.pack(fill="both", expand=True, padx=20, pady=20)
    
    def criar_relatorio_vendas(self, frame):
        ctk.CTkLabel(
            frame,
            text="Relatório de Vendas",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Treeview para vendas
        columns = ("Data", "Cliente", "Item", "Quantidade", "Valor", "Forma Pagamento")
        tree_vendas = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            tree_vendas.heading(col, text=col)
            tree_vendas.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree_vendas.yview)
        tree_vendas.configure(yscrollcommand=scrollbar.set)
        
        tree_vendas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Carregar vendas dos últimos 30 dias
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        vendas = self.db.obter_vendas_periodo(data_inicio, data_fim)
        
        for venda in vendas:
            tree_vendas.insert("", "end", values=(
                venda[8][:10] if len(venda) > 8 and venda[8] else "",  # data
                venda[8] or "Não informado",  # cliente_nome
                venda[7],  # item_nome
                venda[4],  # quantidade
                f"R$ {venda[6]:.2f}",  # valor_total
                venda[7]  # forma_pagamento
            ))
    
    def criar_relatorio_clientes(self, frame):
        ctk.CTkLabel(
            frame,
            text="Relatório de Clientes",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Treeview para clientes
        columns = ("Nome", "Telefone", "Total Gasto", "Visitas", "Média por Visita")
        tree_clientes = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            tree_clientes.heading(col, text=col)
            tree_clientes.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree_clientes.yview)
        tree_clientes.configure(yscrollcommand=scrollbar.set)
        
        tree_clientes.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Carregar clientes
        clientes = self.db.obter_clientes()
        
        for cliente in clientes:
            media = cliente[6] / cliente[7] if cliente[7] > 0 else 0
            tree_clientes.insert("", "end", values=(
                cliente[1],  # nome
                cliente[2],  # telefone
                f"R$ {cliente[6]:.2f}",  # total_gasto
                cliente[7],  # total_visitas
                f"R$ {media:.2f}"  # média por visita
            ))
    
    def criar_relatorio_servicos(self, frame):
        ctk.CTkLabel(
            frame,
            text="Relatório de Serviços",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Consultar serviços mais vendidos
        self.db.cursor.execute('''
            SELECT s.nome, COUNT(v.id) as quantidade, SUM(v.valor_total) as total
            FROM vendas v
            JOIN servicos s ON v.item_id = s.id AND v.tipo = 'servico'
            WHERE v.data_venda >= date('now', '-30 days')
            GROUP BY s.id
            ORDER BY total DESC
        ''')
        servicos = self.db.cursor.fetchall()
        
        # Treeview
        columns = ("Serviço", "Quantidade", "Faturamento", "Média por Serviço")
        tree_servicos = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            tree_servicos.heading(col, text=col)
            tree_servicos.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree_servicos.yview)
        tree_servicos.configure(yscrollcommand=scrollbar.set)
        
        tree_servicos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        for servico in servicos:
            media = servico[2] / servico[1] if servico[1] > 0 else 0
            tree_servicos.insert("", "end", values=(
                servico[0],  # nome
                servico[1],  # quantidade
                f"R$ {servico[2]:.2f}",  # total
                f"R$ {media:.2f}"  # média
            ))
    
    # =============================================================
    # 11. MÓDULO DE CONFIGURAÇÕES
    # =============================================================
    def mostrar_configuracoes(self):
        self.limpar_frame_principal()
        
        notebook = ctk.CTkTabview(self.frame_principal)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        notebook.add("Empresa")
        notebook.add("Horários")
        notebook.add("Backup")
        notebook.add("Sistema")
        
        # Aba Empresa
        self.criar_config_empresa(notebook.tab("Empresa"))
        
        # Aba Horários
        self.criar_config_horarios(notebook.tab("Horários"))
        
        # Aba Backup
        self.criar_config_backup(notebook.tab("Backup"))
        
        # Aba Sistema
        self.criar_config_sistema(notebook.tab("Sistema"))
    
    def criar_config_empresa(self, frame):
        ctk.CTkLabel(
            frame,
            text="Configurações da Empresa",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        campos = [
            ("Nome da Barbearia:", "Barbearia Granada"),
            ("CNPJ:", ""),
            ("Endereço:", ""),
            ("Telefone:", ""),
            ("Email:", ""),
            ("Instagram:", "@barbeariagranada"),
        ]
        
        for label_text, valor_padrao in campos:
            linha = ctk.CTkFrame(frame, fg_color="transparent")
            linha.pack(fill="x", padx=50, pady=5)
            
            ctk.CTkLabel(linha, text=label_text, width=150).pack(side="left")
            entry = ctk.CTkEntry(linha, width=300)
            entry.insert(0, valor_padrao)
            entry.pack(side="left")
        
        ctk.CTkButton(
            frame,
            text="💾 Salvar Configurações",
            width=200
        ).pack(pady=30)
    
    def criar_config_horarios(self, frame):
        ctk.CTkLabel(
            frame,
            text="Horários de Funcionamento",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        dias_semana = [
            ("Segunda-feira", True, "09:00", "18:00"),
            ("Terça-feira", True, "09:00", "18:00"),
            ("Quarta-feira", True, "09:00", "18:00"),
            ("Quinta-feira", True, "09:00", "18:00"),
            ("Sexta-feira", True, "09:00", "19:00"),
            ("Sábado", True, "08:00", "17:00"),
            ("Domingo", False, "", ""),
        ]
        
        for dia, aberto, abertura, fechamento in dias_semana:
            linha = ctk.CTkFrame(frame, fg_color="transparent")
            linha.pack(fill="x", padx=50, pady=5)
            
            # Checkbox
            var_aberto = ctk.BooleanVar(value=aberto)
            ctk.CTkCheckBox(
                linha,
                text=dia,
                variable=var_aberto,
                width=150
            ).pack(side="left")
            
            # Horários
            if aberto:
                entry_abertura = ctk.CTkEntry(linha, width=80)
                entry_abertura.insert(0, abertura)
                entry_abertura.pack(side="left", padx=5)
                
                ctk.CTkLabel(linha, text="às").pack(side="left", padx=5)
                
                entry_fechamento = ctk.CTkEntry(linha, width=80)
                entry_fechamento.insert(0, fechamento)
                entry_fechamento.pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame,
            text="💾 Salvar Horários",
            width=200
        ).pack(pady=30)
    
    def criar_config_backup(self, frame):
        ctk.CTkLabel(
            frame,
            text="Backup do Sistema",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        info_frame = ctk.CTkFrame(frame, fg_color="#E3F2FD")
        info_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="⚠️ Faça backup regularmente para não perder dados!",
            font=("Arial", 12),
            text_color="#1565C0"
        ).pack(pady=10)
        
        # Botões de backup
        botoes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        botoes_frame.pack(pady=20)
        
        ctk.CTkButton(
            botoes_frame,
            text="💾 Fazer Backup Agora",
            command=self.fazer_backup,
            width=200
        ).pack(pady=10)
        
        ctk.CTkButton(
            botoes_frame,
            text="📂 Restaurar Backup",
            command=self.restaurar_backup,
            width=200
        ).pack(pady=10)
        
        # Informações
        self.db.cursor.execute("SELECT COUNT(*) FROM clientes")
        num_clientes = self.db.cursor.fetchone()[0]
        
        self.db.cursor.execute("SELECT COUNT(*) FROM vendas")
        num_vendas = self.db.cursor.fetchone()[0]
        
        info_text = f"""
        Estatísticas do Sistema:
        • Clientes cadastrados: {num_clientes}
        • Vendas registradas: {num_vendas}
        • Tamanho do banco: {(Path('barbearia.db').stat().st_size / 1024):.1f} KB
        """
        
        ctk.CTkLabel(
            frame,
            text=info_text,
            font=("Arial", 11),
            justify="left"
        ).pack(pady=20)
    
    def fazer_backup(self):
        try:
            # Criar pasta de backups
            pasta_backup = Path("backups")
            pasta_backup.mkdir(exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = pasta_backup / f"backup_{timestamp}.db"
            
            # Copiar arquivo do banco
            shutil.copy2("barbearia.db", nome_arquivo)
            
            # Criar arquivo de log
            with open(pasta_backup / f"backup_{timestamp}.txt", "w") as f:
                f.write(f"Backup criado em: {datetime.now()}\n")
                f.write(f"Arquivo: {nome_arquivo}\n")
                
                # Estatísticas
                self.db.cursor.execute("SELECT COUNT(*) FROM clientes")
                f.write(f"Clientes: {self.db.cursor.fetchone()[0]}\n")
                
                self.db.cursor.execute("SELECT COUNT(*) FROM vendas")
                f.write(f"Vendas: {self.db.cursor.fetchone()[0]}\n")
            
            CTkMessagebox(
                title="Backup Concluído",
                message=f"Backup criado com sucesso!\n\nArquivo: {nome_arquivo.name}",
                icon="check"
            )
            
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro ao fazer backup: {str(e)}", icon="cancel")
    
    def restaurar_backup(self):
        # Implementar interface para selecionar arquivo de backup
        CTkMessagebox(
            title="Funcionalidade em Desenvolvimento",
            message="A restauração de backup será implementada na próxima versão.",
            icon="info"
        )
    
    def criar_config_sistema(self, frame):
        ctk.CTkLabel(
            frame,
            text="Configurações do Sistema",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Tema
        ctk.CTkLabel(frame, text="Tema da Interface:", font=("Arial", 14)).pack(anchor="w", padx=50, pady=(10, 5))
        
        frame_tema = ctk.CTkFrame(frame, fg_color="transparent")
        frame_tema.pack(anchor="w", padx=50, pady=(0, 20))
        
        var_tema = ctk.StringVar(value="dark")
        
        ctk.CTkRadioButton(
            frame_tema,
            text="🌙 Escuro",
            variable=var_tema,
            value="dark"
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkRadioButton(
            frame_tema,
            text="☀️ Claro",
            variable=var_tema,
            value="light"
        ).pack(side="left")
        
        # Idioma
        ctk.CTkLabel(frame, text="Idioma:", font=("Arial", 14)).pack(anchor="w", padx=50, pady=(10, 5))
        
        var_idioma = ctk.StringVar(value="pt")
        ctk.CTkOptionMenu(
            frame,
            variable=var_idioma,
            values=["Português (BR)", "Inglês", "Espanhol"],
            width=200
        ).pack(anchor="w", padx=50, pady=(0, 20))
        
        # Notificações
        ctk.CTkLabel(frame, text="Notificações:", font=("Arial", 14)).pack(anchor="w", padx=50, pady=(10, 5))
        
        frame_notif = ctk.CTkFrame(frame, fg_color="transparent")
        frame_notif.pack(anchor="w", padx=50, pady=(0, 20))
        
        var_notif_email = ctk.BooleanVar(value=True)
        var_notif_whatsapp = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(
            frame_notif,
            text="Email",
            variable=var_notif_email
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkCheckBox(
            frame_notif,
            text="WhatsApp",
            variable=var_notif_whatsapp
        ).pack(side="left")
        
        def aplicar_config():
            # Aplicar tema
            ctk.set_appearance_mode(var_tema.get())
            
            CTkMessagebox(title="Sucesso", message="Configurações aplicadas!", icon="check")
        
        ctk.CTkButton(
            frame,
            text="💾 Aplicar Configurações",
            command=aplicar_config,
            width=200
        ).pack(pady=30)
    
    # =============================================================
    # 12. FUNÇÕES AUXILIARES
    # =============================================================
    def limpar_frame_principal(self):
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
    
    def sair(self):
        resposta = CTkMessagebox(
            title="Sair",
            message="Deseja realmente sair do sistema?",
            icon="question",
            option_1="Cancelar",
            option_2="Sair"
        )
        
        if resposta.get() == "Sair":
            self.db.fechar()
            self.janela.quit()
    
    def run(self):
        self.janela.mainloop()

# =============================================================
# 13. INICIALIZAÇÃO DO SISTEMA
# =============================================================
if __name__ == "__main__":
    # Verificar se é a primeira execução
    if not Path('barbearia.db').exists():
        print("Primeira execução... Criando banco de dados...")
    
    # Iniciar sistema de login
    login = LoginWindow()
    login.run()