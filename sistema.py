import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import sqlite3
from datetime import datetime, timedelta
from tkinter import ttk, filedialog
from pathlib import Path
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('Agg')

# =============================================================
# BANCO DE DADOS COMPLETO
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
                tipo TEXT NOT NULL,
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
        
        # Tabela de caixa
        self.cursor.execute('''
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
        
        # Inserir admin padrão
        self.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha, tipo) VALUES (?, ?, ?, ?)",
                ('Administrador', 'admin', 'admin123', 'admin')
            )
        
        self.conn.commit()
    
    # ========== SERVIÇOS ==========
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
    
    def obter_servico_por_id(self, servico_id):
        self.cursor.execute("SELECT * FROM servicos WHERE id = ?", (servico_id,))
        return self.cursor.fetchone()
    
    def atualizar_servico(self, servico_id, nome, valor, duracao, ativo=1):
        self.cursor.execute(
            "UPDATE servicos SET nome = ?, valor = ?, duracao = ?, ativo = ? WHERE id = ?",
            (nome, valor, duracao, ativo, servico_id)
        )
        self.conn.commit()
    
    def excluir_servico(self, servico_id):
        self.cursor.execute("DELETE FROM servicos WHERE id = ?", (servico_id,))
        self.conn.commit()
    
    # ========== PRODUTOS ==========
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
    
    def obter_produto_por_id(self, produto_id):
        self.cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return self.cursor.fetchone()
    
    def atualizar_produto(self, produto_id, nome, valor_venda, valor_custo, estoque, estoque_minimo, ativo=1):
        self.cursor.execute(
            """UPDATE produtos 
               SET nome = ?, valor_venda = ?, valor_custo = ?, estoque = ?, estoque_minimo = ?, ativo = ?
               WHERE id = ?""",
            (nome, valor_venda, valor_custo, estoque, estoque_minimo, ativo, produto_id)
        )
        self.conn.commit()
    
    def excluir_produto(self, produto_id):
        self.cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        self.conn.commit()
    
    def atualizar_estoque(self, produto_id, quantidade):
        self.cursor.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (quantidade, produto_id)
        )
        self.conn.commit()
    
    # ========== CLIENTES ==========
    def adicionar_cliente(self, nome, telefone, email="", data_nascimento=None, observacoes=""):
        self.cursor.execute(
            """INSERT INTO clientes (nome, telefone, email, data_nascimento, observacoes) 
               VALUES (?, ?, ?, ?, ?)""",
            (nome, telefone, email, data_nascimento, observacoes)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_clientes(self):
        self.cursor.execute("SELECT * FROM clientes ORDER BY nome")
        return self.cursor.fetchall()
    
    def buscar_cliente_por_telefone(self, telefone):
        self.cursor.execute("SELECT * FROM clientes WHERE telefone = ?", (telefone,))
        return self.cursor.fetchone()
    
    def buscar_cliente_por_nome(self, nome):
        self.cursor.execute("SELECT * FROM clientes WHERE nome LIKE ? ORDER BY nome", (f'%{nome}%',))
        return self.cursor.fetchall()
    
    def atualizar_cliente(self, cliente_id, **kwargs):
        if not kwargs:
            return
        
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(cliente_id)
        
        query = f"UPDATE clientes SET {set_clause} WHERE id = ?"
        self.cursor.execute(query, values)
        self.conn.commit()
    
    def excluir_cliente(self, cliente_id):
        self.cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        self.conn.commit()
    
    # ========== AGENDAMENTOS ==========
    def adicionar_agendamento(self, cliente_id, servico_id, data, hora, profissional, valor, observacoes=""):
        self.cursor.execute(
            """INSERT INTO agendamentos 
               (cliente_id, servico_id, data, hora, profissional, valor, observacoes) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cliente_id, servico_id, data, hora, profissional, valor, observacoes)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obter_agendamentos_do_dia(self, data=None):
        if data is None:
            data = datetime.now().strftime("%Y-%m-%d")
        
        self.cursor.execute('''
            SELECT a.*, c.nome as cliente_nome, c.telefone, s.nome as servico_nome 
            FROM agendamentos a
            LEFT JOIN clientes c ON a.cliente_id = c.id
            LEFT JOIN servicos s ON a.servico_id = s.id
            WHERE a.data = ?
            ORDER BY a.hora
        ''', (data,))
        return self.cursor.fetchall()
    
    def obter_agendamentos_periodo(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT a.*, c.nome as cliente_nome, s.nome as servico_nome 
            FROM agendamentos a
            LEFT JOIN clientes c ON a.cliente_id = c.id
            LEFT JOIN servicos s ON a.servico_id = s.id
            WHERE a.data BETWEEN ? AND ?
            ORDER BY a.data, a.hora
        ''', (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    def atualizar_status_agendamento(self, agendamento_id, status):
        self.cursor.execute(
            "UPDATE agendamentos SET status = ? WHERE id = ?",
            (status, agendamento_id)
        )
        self.conn.commit()
    
    def excluir_agendamento(self, agendamento_id):
        """EXCLUI agendamento pelo ID"""
        self.cursor.execute("DELETE FROM agendamentos WHERE id = ?", (agendamento_id,))
        self.conn.commit()
    
    # ========== VENDAS ==========
    def registrar_venda(self, cliente_id, tipo, item_id, quantidade, valor_unitario, forma_pagamento):
        valor_total = valor_unitario * quantidade
        
        self.cursor.execute(
            """INSERT INTO vendas 
               (cliente_id, tipo, item_id, quantidade, valor_unitario, valor_total, forma_pagamento) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cliente_id, tipo, item_id, quantidade, valor_unitario, valor_total, forma_pagamento)
        )
        
        if cliente_id:
            self.cursor.execute(
                "UPDATE clientes SET total_gasto = total_gasto + ?, total_visitas = total_visitas + 1 WHERE id = ?",
                (valor_total, cliente_id)
            )
        
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
    
    def obter_total_vendas_periodo(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM vendas 
            WHERE date(data_venda) BETWEEN ? AND ?
        ''', (data_inicio, data_fim))
        return self.cursor.fetchone()[0] or 0
    
    # ========== DESPESAS ==========
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
    
    def obter_total_despesas_periodo(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT COALESCE(SUM(valor), 0) 
            FROM despesas 
            WHERE data BETWEEN ? AND ?
        ''', (data_inicio, data_fim))
        return self.cursor.fetchone()[0] or 0
    
    # ========== CAIXA ==========
    def abrir_caixa(self, valor_inicial):
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            "INSERT INTO caixa (data, valor_inicial, status) VALUES (?, ?, 'aberto')",
            (hoje, valor_inicial)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def fechar_caixa(self, valor_final):
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            """UPDATE caixa 
               SET valor_final = ?, status = 'fechado', data_fechamento = CURRENT_TIMESTAMP
               WHERE data = ? AND status = 'aberto'""",
            (valor_final, hoje)
        )
        self.conn.commit()
    
    def caixa_esta_aberto(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            "SELECT COUNT(*) FROM caixa WHERE data = ? AND status = 'aberto'",
            (hoje,)
        )
        return self.cursor.fetchone()[0] > 0
    
    def obter_caixa_hoje(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            "SELECT * FROM caixa WHERE data = ?",
            (hoje,)
        )
        return self.cursor.fetchone()
    
    # ========== RELATÓRIOS ==========
    def obter_resumo_financeiro(self, data_inicio, data_fim):
        total_vendas = self.obter_total_vendas_periodo(data_inicio, data_fim)
        total_despesas = self.obter_total_despesas_periodo(data_inicio, data_fim)
        lucro = total_vendas - total_despesas
        
        return {
            'total_vendas': total_vendas,
            'total_despesas': total_despesas,
            'lucro': lucro
        }
    
    def obter_top_clientes(self, limite=10):
        self.cursor.execute('''
            SELECT nome, total_gasto, total_visitas 
            FROM clientes 
            WHERE total_visitas > 0
            ORDER BY total_gasto DESC
            LIMIT ?
        ''', (limite,))
        return self.cursor.fetchall()
    
    def obter_servicos_mais_vendidos(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT s.nome, COUNT(v.id) as quantidade, SUM(v.valor_total) as total
            FROM vendas v
            JOIN servicos s ON v.item_id = s.id AND v.tipo = 'servico'
            WHERE date(v.data_venda) BETWEEN ? AND ?
            GROUP BY s.id
            ORDER BY total DESC
        ''', (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    def obter_produtos_mais_vendidos(self, data_inicio, data_fim):
        self.cursor.execute('''
            SELECT p.nome, SUM(v.quantidade) as quantidade, SUM(v.valor_total) as total
            FROM vendas v
            JOIN produtos p ON v.item_id = p.id AND v.tipo = 'produto'
            WHERE date(v.data_venda) BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY total DESC
        ''', (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    def fechar(self):
        self.conn.close()

# =============================================================
# SISTEMA DE LOGIN
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
        ctk.CTkLabel(
            self.janela,
            text="Barbearia Granada",
            font=("Arial", 28, "bold"),
            text_color="#4CC9F0"
        ).pack(pady=(40, 20))
        
        frame_campos = ctk.CTkFrame(self.janela, fg_color="transparent")
        frame_campos.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(frame_campos, text="Usuário:").pack(anchor="w", pady=(0, 5))
        self.entry_usuario = ctk.CTkEntry(frame_campos, placeholder_text="Digite seu usuário")
        self.entry_usuario.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame_campos, text="Senha:").pack(anchor="w", pady=(0, 5))
        self.entry_senha = ctk.CTkEntry(frame_campos, placeholder_text="Digite sua senha", show="•")
        self.entry_senha.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            self.janela,
            text="Entrar",
            command=self.fazer_login,
            height=40,
            font=("Arial", 14)
        ).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(
            self.janela,
            text="Usuário padrão: admin\nSenha padrão: admin123",
            text_color="gray",
            font=("Arial", 10)
        ).pack(side="bottom", pady=20)
    
    def fazer_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        
        self.db.cursor.execute(
            "SELECT id, nome, tipo FROM usuarios WHERE usuario = ? AND senha = ? AND ativo = 1",
            (usuario, senha)
        )
        usuario_info = self.db.cursor.fetchone()
        
        if usuario_info:
            self.janela.destroy()
            app = BarbeariaApp(usuario_info)
            app.run()
        else:
            if usuario == "admin" and senha == "admin123":
                self.janela.destroy()
                app = BarbeariaApp((1, "Administrador", "admin"))
                app.run()
            else:
                CTkMessagebox(title="Erro", message="Usuário ou senha incorretos!", icon="cancel")
    
    def run(self):
        self.janela.mainloop()

# =============================================================
# APLICAÇÃO PRINCIPAL COMPLETA COM TODAS CORREÇÕES
# =============================================================
class BarbeariaApp:
    def __init__(self, usuario_info):
        self.usuario_id, self.usuario_nome, self.usuario_tipo = usuario_info
        self.db = Database()
        
        self.setup_janela()
        self.setup_menu()
        self.setup_dashboard()
    
    def setup_janela(self):
        self.janela = ctk.CTk()
        self.janela.title(f"Barbearia Granada - {self.usuario_nome}")
        self.janela.geometry("1400x800")
        self.janela.minsize(1200, 700)
        
        self.janela.grid_rowconfigure(0, weight=1)
        self.janela.grid_columnconfigure(1, weight=1)
    
    def setup_menu(self):
        self.frame_menu = ctk.CTkFrame(self.janela, width=250, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_propagate(False)
        
        # Logo
        ctk.CTkLabel(
            self.frame_menu,
            text="Barbearia\nGranada",
            font=("Arial", 24, "bold"),
            text_color="#4CC9F0"
        ).pack(pady=(30, 10))
        
        # Info usuário
        ctk.CTkLabel(
            self.frame_menu,
            text=f"👤 {self.usuario_nome}",
            font=("Arial", 12),
            text_color="#CCCCCC"
        ).pack(pady=(0, 20))
        
        # Menu
        botoes_menu = [
            ("🏠 Dashboard", self.mostrar_dashboard),
            ("✂️ Serviços", self.mostrar_servicos),
            ("🛍️ Produtos", self.mostrar_produtos),
            ("👥 Clientes", self.mostrar_clientes),
            ("📅 Agendamentos", self.mostrar_agendamentos),
            ("💰 Caixa", self.mostrar_caixa),
            ("🛒 Nova Venda", self.mostrar_nova_venda),
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
        
        # Sair
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
    # 1. DASHBOARD COMPLETO
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
            text=datetime.now().strftime("%d/%m/%Y %H:%M"),
            font=("Arial", 14),
            text_color="gray"
        ).pack(side="right")
        
        # Métricas
        self.criar_metricas_rapidas()
        
        # Agendamentos do dia
        self.criar_agendamentos_hoje()
        
        # Produtos baixo estoque
        self.criar_alerta_estoque()
        
        # Gráfico simples
        self.criar_grafico_vendas()
    
    def criar_metricas_rapidas(self):
        frame_metricas = ctk.CTkFrame(self.frame_principal)
        frame_metricas.pack(fill="x", padx=20, pady=(0, 20))
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Agendamentos hoje
        agendamentos = self.db.obter_agendamentos_do_dia(hoje)
        agendamentos_hoje = len([a for a in agendamentos if a[7] == 'agendado'])
        
        # Clientes novos hoje
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM clientes WHERE date(data_cadastro) = date('now')"
        )
        clientes_novos = self.db.cursor.fetchone()[0] or 0
        
        # Vendas hoje
        vendas_hoje = self.db.obter_total_vendas_periodo(hoje, hoje)
        
        # Produtos baixo estoque
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM produtos WHERE estoque <= estoque_minimo AND ativo = 1"
        )
        produtos_baixo_estoque = self.db.cursor.fetchone()[0] or 0
        
        metricas = [
            ("📅 Agendamentos Hoje", str(agendamentos_hoje), "#2196F3"),
            ("👥 Clientes Novos", str(clientes_novos), "#4CAF50"),
            ("💰 Vendas Hoje", f"R$ {vendas_hoje:,.2f}", "#FF9800"),
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
            text="📅 Agendamentos de Hoje",
            font=("Arial", 18, "bold")
        ).pack(pady=15)
        
        # Treeview
        columns = ("Hora", "Cliente", "Telefone", "Serviço", "Profissional", "Status")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        
        col_widths = {"Hora": 80, "Cliente": 150, "Telefone": 120, "Serviço": 150, "Profissional": 120, "Status": 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Carregar dados
        agendamentos = self.db.obter_agendamentos_do_dia()
        for ag in agendamentos:
            status_color = {
                'agendado': 'blue',
                'confirmado': 'green',
                'finalizado': 'gray',
                'cancelado': 'red'
            }.get(ag[7], 'black')
            
            tree.insert("", "end", values=(
                ag[4],  # hora
                ag[11],  # cliente_nome
                ag[12],  # telefone
                ag[13],  # servico_nome
                ag[6],   # profissional
                ag[7]    # status
            ), tags=(status_color,))
        
        # Configurar cores
        tree.tag_configure('blue', foreground='blue')
        tree.tag_configure('green', foreground='green')
        tree.tag_configure('gray', foreground='gray')
        tree.tag_configure('red', foreground='red')
        
        # Botões
        frame_botoes = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=10, pady=(0, 10))
        
        botoes = [
            ("✅ Confirmar", self.confirmar_agendamento_dash),
            ("💰 Finalizar", self.finalizar_agendamento_dash),
            ("❌ Cancelar", self.cancelar_agendamento_dash),
        ]
        
        for texto, comando in botoes:
            ctk.CTkButton(
                frame_botoes,
                text=texto,
                command=comando,
                width=120
            ).pack(side="left", padx=5)
    
    def criar_alerta_estoque(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="⚠️ Produtos com Baixo Estoque",
            font=("Arial", 16, "bold"),
            text_color="#F44336"
        ).pack(pady=(10, 5))
        
        produtos = self.db.obter_produtos()
        produtos_baixo = [p for p in produtos if p[4] <= p[5] and p[6] == 1]
        
        if produtos_baixo:
            for produto in produtos_baixo[:5]:
                frame_produto = ctk.CTkFrame(frame, fg_color="#FFF3E0")
                frame_produto.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(
                    frame_produto,
                    text=f"{produto[1]} - Estoque: {produto[4]} (Mínimo: {produto[5]})",
                    font=("Arial", 12),
                    text_color="black"
                ).pack(pady=5)
            
            if len(produtos_baixo) > 5:
                ctk.CTkLabel(
                    frame,
                    text=f"... e mais {len(produtos_baixo) - 5} produtos",
                    font=("Arial", 11),
                    text_color="gray"
                ).pack(pady=5)
        else:
            ctk.CTkLabel(
                frame,
                text="✅ Todos os produtos estão com estoque adequado",
                font=("Arial", 12),
                text_color="#4CAF50"
            ).pack(pady=10)
    
    def criar_grafico_vendas(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="📈 Vendas dos Últimos 7 Dias",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        try:
            datas = []
            valores = []
            
            for i in range(6, -1, -1):
                data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                total = self.db.obter_total_vendas_periodo(data, data)
                datas.append(data[8:10] + "/" + data[5:7])
                valores.append(total)
            
            fig, ax = plt.subplots(figsize=(8, 4), facecolor='#2B2B2B')
            ax.bar(datas, valores, color='#4CC9F0')
            ax.set_facecolor('#2B2B2B')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.set_ylabel('Valor (R$)', color='white')
            ax.set_title('Vendas Diárias', color='white', pad=20)
            
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            ctk.CTkLabel(
                frame,
                text=f"Erro ao gerar gráfico: {str(e)}",
                text_color="#F44336"
            ).pack(pady=20)
    
    # =============================================================
    # 2. SERVIÇOS
    # =============================================================
    def mostrar_servicos(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="✂️ Gerenciar Serviços",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        frame_conteudo = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_conteudo.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Lista
        frame_lista = ctk.CTkFrame(frame_conteudo)
        frame_lista.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            frame_lista,
            text="Serviços Cadastrados",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 5))
        
        columns = ("ID", "Nome", "Valor", "Duração")
        self.tree_servicos = ttk.Treeview(
            frame_lista,
            columns=columns,
            show="headings",
            height=15
        )
        
        col_widths = {"ID": 50, "Nome": 200, "Valor": 100, "Duração": 80}
        for col in columns:
            self.tree_servicos.heading(col, text=col)
            self.tree_servicos.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_servicos.yview)
        self.tree_servicos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_servicos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Formulário
        frame_form = ctk.CTkFrame(frame_conteudo, width=350)
        frame_form.pack(side="right", fill="y", padx=(10, 0))
        frame_form.pack_propagate(False)
        
        ctk.CTkLabel(
            frame_form,
            text="Adicionar/Editar Serviço",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(frame_form, fg_color="transparent")
        campos_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Campos
        ctk.CTkLabel(campos_frame, text="Nome do Serviço:").pack(anchor="w", pady=(0, 5))
        self.entry_nome_servico = ctk.CTkEntry(campos_frame, width=300)
        self.entry_nome_servico.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(campos_frame, text="Valor (R$):").pack(anchor="w", pady=(0, 5))
        self.entry_valor_servico = ctk.CTkEntry(campos_frame, width=150)
        self.entry_valor_servico.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(campos_frame, text="Duração (minutos):").pack(anchor="w", pady=(0, 5))
        self.entry_duracao_servico = ctk.CTkEntry(campos_frame, width=150)
        self.entry_duracao_servico.pack(anchor="w", pady=(0, 15))
        
        # Botões
        frame_botoes = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botoes.pack(pady=20)
        
        ctk.CTkButton(
            frame_botoes,
            text="➕ Adicionar Serviço",
            command=self.adicionar_servico,
            width=200,
            height=35
        ).pack(pady=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="✏️ Editar Serviço",
            command=self.editar_servico,
            width=200,
            height=35
        ).pack(pady=5)
        
        ctk.CTkButton(
            frame_botoes,
            text="🗑️ Excluir Serviço",
            command=self.excluir_servico,
            fg_color="#D44336",
            hover_color="#B71C1C",
            width=200,
            height=35
        ).pack(pady=5)
        
        self.carregar_servicos()
    
    def carregar_servicos(self):
        for item in self.tree_servicos.get_children():
            self.tree_servicos.delete(item)
        
        servicos = self.db.obter_servicos(apenas_ativos=True)
        for servico in servicos:
            self.tree_servicos.insert("", "end", values=(
                servico[0],
                servico[1],
                f"R$ {servico[2]:.2f}",
                f"{servico[3]} min"
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
            
            self.entry_nome_servico.delete(0, "end")
            self.entry_valor_servico.delete(0, "end")
            self.entry_duracao_servico.delete(0, "end")
            
            self.carregar_servicos()
            CTkMessagebox(title="Sucesso", message="Serviço adicionado!", icon="check")
            
        except ValueError:
            CTkMessagebox(title="Erro", message="Valores inválidos!", icon="cancel")
    
    def editar_servico(self):
        selecionado = self.tree_servicos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um serviço!", icon="warning")
            return
        
        item = self.tree_servicos.item(selecionado[0])
        servico_id = item['values'][0]
        servico = self.db.obter_servico_por_id(servico_id)
        
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Editar Serviço")
        janela.geometry("400x400")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(janela, text="Editar Serviço", font=("Arial", 18, "bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(pady=20, padx=40, fill="both")
        
        ctk.CTkLabel(campos_frame, text="Nome:").pack(anchor="w")
        entry_nome = ctk.CTkEntry(campos_frame, width=300)
        entry_nome.insert(0, servico[1])
        entry_nome.pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(campos_frame, text="Valor (R$):").pack(anchor="w")
        entry_valor = ctk.CTkEntry(campos_frame, width=150)
        entry_valor.insert(0, str(servico[2]))
        entry_valor.pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(campos_frame, text="Duração (min):").pack(anchor="w")
        entry_duracao = ctk.CTkEntry(campos_frame, width=150)
        entry_duracao.insert(0, str(servico[3]))
        entry_duracao.pack(anchor="w", pady=(0, 20))
        
        def salvar():
            try:
                nome = entry_nome.get().strip()
                valor = float(entry_valor.get().replace(',', '.'))
                duracao = int(entry_duracao.get())
                
                resposta = CTkMessagebox(
                    title="Confirmar",
                    message="Deseja salvar as alterações?",
                    icon="question",
                    option_1="Cancelar",
                    option_2="Salvar"
                )
                
                if resposta.get() == "Salvar":
                    self.db.atualizar_servico(servico_id, nome, valor, duracao)
                    self.carregar_servicos()
                    janela.destroy()
                    CTkMessagebox(title="Sucesso", message="Serviço atualizado!", icon="check")
                    
            except ValueError:
                CTkMessagebox(title="Erro", message="Valores inválidos!", icon="cancel")
        
        ctk.CTkButton(janela, text="💾 Salvar", command=salvar, width=200, height=40).pack(pady=20)
        ctk.CTkButton(janela, text="❌ Cancelar", command=janela.destroy, fg_color="gray", width=200).pack()
    
    def excluir_servico(self):
        selecionado = self.tree_servicos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um serviço!", icon="warning")
            return
        
        item = self.tree_servicos.item(selecionado[0])
        servico_id = item['values'][0]
        servico_nome = item['values'][1]
        
        resposta = CTkMessagebox(
            title="Confirmar Exclusão",
            message=f"Excluir o serviço '{servico_nome}'?\n\nEsta ação não pode ser desfeita!",
            icon="warning",
            option_1="Cancelar",
            option_2="Excluir"
        )
        
        if resposta.get() == "Excluir":
            self.db.excluir_servico(servico_id)
            self.carregar_servicos()
            CTkMessagebox(title="Sucesso", message="Serviço excluído!", icon="check")
    
    # =============================================================
    # 3. PRODUTOS
    # =============================================================
    def mostrar_produtos(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="🛍️ Gerenciar Produtos",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        frame_conteudo = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_conteudo.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Lista
        frame_lista = ctk.CTkFrame(frame_conteudo)
        frame_lista.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(frame_lista, text="Produtos Cadastrados", font=("Arial", 16, "bold")).pack(pady=(10, 5))
        
        columns = ("ID", "Nome", "Venda", "Custo", "Estoque", "Mínimo")
        self.tree_produtos = ttk.Treeview(frame_lista, columns=columns, show="headings", height=15)
        
        col_widths = {"ID": 50, "Nome": 200, "Venda": 80, "Custo": 80, "Estoque": 70, "Mínimo": 70}
        for col in columns:
            self.tree_produtos.heading(col, text=col)
            self.tree_produtos.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_produtos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Formulário
        frame_form = ctk.CTkFrame(frame_conteudo, width=350)
        frame_form.pack(side="right", fill="y", padx=(10, 0))
        frame_form.pack_propagate(False)
        
        ctk.CTkLabel(frame_form, text="Adicionar/Editar Produto", font=("Arial", 16, "bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(frame_form, fg_color="transparent")
        campos_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Campos
        campos = [
            ("Nome do Produto:", ctk.CTkEntry(campos_frame, width=300)),
            ("Valor Venda (R$):", ctk.CTkEntry(campos_frame, width=150)),
            ("Valor Custo (R$):", ctk.CTkEntry(campos_frame, width=150)),
            ("Estoque:", ctk.CTkEntry(campos_frame, width=100)),
            ("Estoque Mínimo:", ctk.CTkEntry(campos_frame, width=100)),
        ]
        
        self.entries_produtos = {}
        for i, (label_text, entry) in enumerate(campos):
            ctk.CTkLabel(campos_frame, text=label_text).pack(anchor="w", pady=(0, 5))
            entry.pack(anchor="w", pady=(0, 10 if i < len(campos)-1 else 20))
            self.entries_produtos[label_text] = entry
        
        self.entries_produtos["Estoque Mínimo:"].insert(0, "5")
        
        # Botões
        frame_botoes = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botoes.pack(pady=20)
        
        ctk.CTkButton(frame_botoes, text="➕ Adicionar Produto", command=self.adicionar_produto, width=200, height=35).pack(pady=5)
        ctk.CTkButton(frame_botoes, text="✏️ Editar Produto", command=self.editar_produto, width=200, height=35).pack(pady=5)
        ctk.CTkButton(frame_botoes, text="🗑️ Excluir Produto", command=self.excluir_produto, fg_color="#D44336", width=200, height=35).pack(pady=5)
        
        self.carregar_produtos()
    
    def carregar_produtos(self):
        for item in self.tree_produtos.get_children():
            self.tree_produtos.delete(item)
        
        produtos = self.db.obter_produtos(apenas_ativos=True)
        for produto in produtos:
            self.tree_produtos.insert("", "end", values=(
                produto[0],
                produto[1],
                f"R$ {produto[2]:.2f}",
                f"R$ {produto[3]:.2f}",
                produto[4],
                produto[5]
            ))
    
    def adicionar_produto(self):
        try:
            nome = self.entries_produtos["Nome do Produto:"].get().strip()
            valor_venda = float(self.entries_produtos["Valor Venda (R$):"].get().replace(',', '.'))
            valor_custo = float(self.entries_produtos["Valor Custo (R$):"].get().replace(',', '.'))
            estoque = int(self.entries_produtos["Estoque:"].get())
            estoque_minimo = int(self.entries_produtos["Estoque Mínimo:"].get())
            
            self.db.adicionar_produto(nome, valor_venda, valor_custo, estoque, estoque_minimo)
            
            for entry in self.entries_produtos.values():
                entry.delete(0, "end")
            self.entries_produtos["Estoque Mínimo:"].insert(0, "5")
            
            self.carregar_produtos()
            CTkMessagebox(title="Sucesso", message="Produto adicionado!", icon="check")
            
        except ValueError:
            CTkMessagebox(title="Erro", message="Valores inválidos!", icon="cancel")
    
    def editar_produto(self):
        selecionado = self.tree_produtos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um produto!", icon="warning")
            return
        
        item = self.tree_produtos.item(selecionado[0])
        produto_id = item['values'][0]
        produto = self.db.obter_produto_por_id(produto_id)
        
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Editar Produto")
        janela.geometry("400x450")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(janela, text="Editar Produto", font=("Arial", 18, "bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(pady=20, padx=40, fill="both")
        
        campos = [
            ("Nome:", ctk.CTkEntry(campos_frame, width=300)),
            ("Valor Venda (R$):", ctk.CTkEntry(campos_frame, width=150)),
            ("Valor Custo (R$):", ctk.CTkEntry(campos_frame, width=150)),
            ("Estoque:", ctk.CTkEntry(campos_frame, width=100)),
            ("Estoque Mínimo:", ctk.CTkEntry(campos_frame, width=100)),
        ]
        
        entries = []
        valores = [produto[1], str(produto[2]), str(produto[3]), str(produto[4]), str(produto[5])]
        
        for i, (label_text, entry) in enumerate(campos):
            ctk.CTkLabel(campos_frame, text=label_text).pack(anchor="w", pady=(0, 5))
            entry.insert(0, valores[i])
            entry.pack(anchor="w", pady=(0, 10 if i < len(campos)-1 else 20))
            entries.append(entry)
        
        def salvar():
            try:
                nome = entries[0].get().strip()
                valor_venda = float(entries[1].get().replace(',', '.'))
                valor_custo = float(entries[2].get().replace(',', '.'))
                estoque = int(entries[3].get())
                estoque_minimo = int(entries[4].get())
                
                resposta = CTkMessagebox(
                    title="Confirmar",
                    message="Deseja salvar as alterações?",
                    icon="question",
                    option_1="Cancelar",
                    option_2="Salvar"
                )
                
                if resposta.get() == "Salvar":
                    self.db.atualizar_produto(produto_id, nome, valor_venda, valor_custo, estoque, estoque_minimo)
                    self.carregar_produtos()
                    janela.destroy()
                    CTkMessagebox(title="Sucesso", message="Produto atualizado!", icon="check")
                    
            except ValueError:
                CTkMessagebox(title="Erro", message="Valores inválidos!", icon="cancel")
        
        ctk.CTkButton(janela, text="💾 Salvar", command=salvar, width=200, height=40).pack(pady=20)
        ctk.CTkButton(janela, text="❌ Cancelar", command=janela.destroy, fg_color="gray", width=200).pack()
    
    def excluir_produto(self):
        selecionado = self.tree_produtos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um produto!", icon="warning")
            return
        
        item = self.tree_produtos.item(selecionado[0])
        produto_id = item['values'][0]
        produto_nome = item['values'][1]
        
        resposta = CTkMessagebox(
            title="Confirmar Exclusão",
            message=f"Excluir o produto '{produto_nome}'?\n\nEsta ação não pode ser desfeita!",
            icon="warning",
            option_1="Cancelar",
            option_2="Excluir"
        )
        
        if resposta.get() == "Excluir":
            self.db.excluir_produto(produto_id)
            self.carregar_produtos()
            CTkMessagebox(title="Sucesso", message="Produto excluído!", icon="check")
    
    # =============================================================
    # 4. CLIENTES
    # =============================================================
    def mostrar_clientes(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="👥 Gerenciar Clientes",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Barra de pesquisa
        frame_pesquisa = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_pesquisa.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(frame_pesquisa, text="🔍 Pesquisar:").pack(side="left", padx=(0, 10))
        self.entry_pesquisa_cliente = ctk.CTkEntry(frame_pesquisa, width=300, placeholder_text="Nome ou telefone...")
        self.entry_pesquisa_cliente.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_pesquisa,
            text="Buscar",
            command=self.buscar_clientes,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_pesquisa,
            text="➕ Novo Cliente",
            command=self.abrir_form_cliente,
            fg_color="#4CAF50",
            width=150
        ).pack(side="right")
        
        # Treeview
        frame_tree = ctk.CTkFrame(self.frame_principal)
        frame_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("ID", "Nome", "Telefone", "Email", "Cadastro", "Gasto Total", "Visitas")
        self.tree_clientes = ttk.Treeview(
            frame_tree,
            columns=columns,
            show="headings",
            height=15
        )
        
        col_widths = {"ID": 50, "Nome": 200, "Telefone": 120, "Email": 180, "Cadastro": 100, "Gasto Total": 120, "Visitas": 80}
        for col in columns:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, width=col_widths.get(col, 100))
        
        scrollbar_y = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_clientes.yview)
        scrollbar_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree_clientes.xview)
        self.tree_clientes.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree_clientes.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Botões de ação
        frame_acoes = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_acoes.pack(fill="x", padx=20, pady=(0, 20))
        
        acoes = [
            ("📞 Ligar", self.ligar_cliente),
            ("💬 WhatsApp", self.whatsapp_cliente),
            ("✏️ Editar", self.editar_cliente),
            ("🗑️ Excluir", self.excluir_cliente),
            ("📊 Histórico", self.ver_historico_cliente),
        ]
        
        for texto, comando in acoes:
            ctk.CTkButton(
                frame_acoes,
                text=texto,
                command=comando,
                width=120
            ).pack(side="left", padx=5)
        
        self.carregar_clientes()
    
    def carregar_clientes(self):
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)
        
        clientes = self.db.obter_clientes()
        for cliente in clientes:
            self.tree_clientes.insert("", "end", values=(
                cliente[0],
                cliente[1],
                cliente[2],
                cliente[3] or "",
                cliente[5],
                f"R$ {cliente[6]:.2f}",
                cliente[7]
            ))
    
    def buscar_clientes(self):
        termo = self.entry_pesquisa_cliente.get().lower()
        
        for item in self.tree_clientes.get_children():
            valores = self.tree_clientes.item(item)['values']
            if (termo in str(valores[1]).lower() or 
                termo in str(valores[2]).lower()):
                self.tree_clientes.selection_set(item)
                self.tree_clientes.see(item)
                return
        
        CTkMessagebox(title="Aviso", message="Nenhum cliente encontrado!", icon="warning")
    
    def abrir_form_cliente(self, cliente=None):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Novo Cliente" if not cliente else "Editar Cliente")
        janela.geometry("500x500")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(
            janela,
            text="Cadastrar Cliente" if not cliente else "Editar Cliente",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(padx=40, pady=10, fill="both")
        
        # Campos
        campos = [
            ("Nome completo:", ctk.CTkEntry(campos_frame, width=300)),
            ("Telefone:", ctk.CTkEntry(campos_frame, width=200)),
            ("Email:", ctk.CTkEntry(campos_frame, width=300)),
            ("Data Nasc. (DD/MM/AAAA):", ctk.CTkEntry(campos_frame, width=150)),
            ("Observações:", ctk.CTkEntry(campos_frame, width=300)),
        ]
        
        entries = []
        valores = ["", "", "", "", ""]
        
        if cliente:
            valores = [
                cliente[1], cliente[2], cliente[3] or "",
                cliente[4] or "", cliente[8] or ""
            ]
        
        for i, (label_text, entry) in enumerate(campos):
            ctk.CTkLabel(campos_frame, text=label_text).pack(anchor="w", pady=(10 if i == 0 else 5, 5))
            entry.insert(0, valores[i])
            entry.pack(anchor="w", pady=(0, 10 if i < len(campos)-1 else 20))
            entries.append(entry)
        
        def salvar():
            nome = entries[0].get().strip()
            telefone = entries[1].get().strip()
            email = entries[2].get().strip()
            data_nasc = entries[3].get().strip()
            observacoes = entries[4].get().strip()
            
            if not nome or not telefone:
                CTkMessagebox(title="Erro", message="Nome e telefone são obrigatórios!", icon="cancel")
                return
            
            try:
                if cliente:
                    updates = {
                        'nome': nome,
                        'telefone': telefone,
                        'email': email if email else None,
                        'data_nascimento': data_nasc if data_nasc else None,
                        'observacoes': observacoes
                    }
                    self.db.atualizar_cliente(cliente[0], **updates)
                    mensagem = "Cliente atualizado!"
                else:
                    self.db.adicionar_cliente(nome, telefone, email, data_nasc if data_nasc else None, observacoes)
                    mensagem = "Cliente cadastrado!"
                
                self.carregar_clientes()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message=mensagem, icon="check")
                
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro: {str(e)}", icon="cancel")
        
        ctk.CTkButton(
            janela,
            text="💾 Salvar",
            command=salvar,
            width=200,
            height=40
        ).pack(pady=20)
    
    def editar_cliente(self):
        selecionado = self.tree_clientes.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um cliente!", icon="warning")
            return
        
        item = self.tree_clientes.item(selecionado[0])
        cliente_id = item['values'][0]
        
        self.db.cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cliente = self.db.cursor.fetchone()
        
        if cliente:
            self.abrir_form_cliente(cliente)
    
    def excluir_cliente(self):
        selecionado = self.tree_clientes.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um cliente!", icon="warning")
            return
        
        item = self.tree_clientes.item(selecionado[0])
        cliente_id = item['values'][0]
        cliente_nome = item['values'][1]
        
        resposta = CTkMessagebox(
            title="Confirmar Exclusão",
            message=f"Excluir o cliente '{cliente_nome}'?\n\nEsta ação não pode ser desfeita!",
            icon="warning",
            option_1="Cancelar",
            option_2="Excluir"
        )
        
        if resposta.get() == "Excluir":
            self.db.excluir_cliente(cliente_id)
            self.carregar_clientes()
            CTkMessagebox(title="Sucesso", message="Cliente excluído!", icon="check")
    
    def ligar_cliente(self):
        selecionado = self.tree_clientes.selection()
        if selecionado:
            item = self.tree_clientes.item(selecionado[0])
            telefone = item['values'][2]
            CTkMessagebox(title="Ligar", message=f"Ligar para: {telefone}", icon="info")
    
    def whatsapp_cliente(self):
        selecionado = self.tree_clientes.selection()
        if selecionado:
            item = self.tree_clientes.item(selecionado[0])
            telefone = item['values'][2]
            CTkMessagebox(title="WhatsApp", message=f"Abrir WhatsApp para: {telefone}", icon="info")
    
    def ver_historico_cliente(self):
        selecionado = self.tree_clientes.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um cliente!", icon="warning")
            return
        
        item = self.tree_clientes.item(selecionado[0])
        cliente_id = item['values'][0]
        cliente_nome = item['values'][1]
        
        janela = ctk.CTkToplevel(self.janela)
        janela.title(f"Histórico - {cliente_nome}")
        janela.geometry("800x500")
        janela.transient(self.janela)
        
        ctk.CTkLabel(janela, text=f"Histórico de {cliente_nome}", font=("Arial", 18, "bold")).pack(pady=20)
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("Data", "Tipo", "Item", "Quantidade", "Valor", "Pagamento")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        data_inicio = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        self.db.cursor.execute('''
            SELECT v.data_venda, v.tipo, 
                   CASE WHEN v.tipo = 'servico' THEN s.nome ELSE p.nome END as item_nome,
                   v.quantidade, v.valor_total, v.forma_pagamento
            FROM vendas v
            LEFT JOIN servicos s ON v.tipo = 'servico' AND v.item_id = s.id
            LEFT JOIN produtos p ON v.tipo = 'produto' AND v.item_id = p.id
            WHERE v.cliente_id = ?
            ORDER BY v.data_venda DESC
        ''', (cliente_id,))
        
        vendas = self.db.cursor.fetchall()
        
        for venda in vendas:
            tree.insert("", "end", values=(
                venda[0][:10],
                "Serviço" if venda[1] == 'servico' else "Produto",
                venda[2],
                venda[3],
                f"R$ {venda[4]:.2f}",
                venda[5]
            ))
    
    # =============================================================
    # 5. AGENDAMENTOS COMPLETO COM EXCLUSÃO FUNCIONAL
    # =============================================================
    def mostrar_agendamentos(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="📅 Agendamentos",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Data selecionada
        self.data_selecionada = datetime.now()
        
        frame_data = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_data.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkButton(
            frame_data,
            text="◀",
            width=40,
            command=lambda: self.mudar_data_agendamento(-1)
        ).pack(side="left", padx=5)
        
        self.label_data_agendamento = ctk.CTkLabel(
            frame_data,
            text=self.data_selecionada.strftime("%A, %d de %B de %Y").title(),
            font=("Arial", 16, "bold")
        )
        self.label_data_agendamento.pack(side="left", padx=20)
        
        ctk.CTkButton(
            frame_data,
            text="▶",
            width=40,
            command=lambda: self.mudar_data_agendamento(1)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_data,
            text="Hoje",
            command=self.ir_para_hoje_agendamento,
            width=60
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            frame_data,
            text="➕ Novo Agendamento",
            command=self.abrir_novo_agendamento,
            fg_color="#4CAF50",
            width=180
        ).pack(side="right")
        
        # Lista de agendamentos
        frame_lista = ctk.CTkFrame(self.frame_principal)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("Hora", "Cliente", "Telefone", "Serviço", "Profissional", "Valor", "Status")
        self.tree_agendamentos = ttk.Treeview(
            frame_lista,
            columns=columns,
            show="headings",
            height=15
        )
        
        col_widths = {"Hora": 80, "Cliente": 150, "Telefone": 120, "Serviço": 150, "Profissional": 120, "Valor": 100, "Status": 100}
        for col in columns:
            self.tree_agendamentos.heading(col, text=col)
            self.tree_agendamentos.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_agendamentos.yview)
        self.tree_agendamentos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_agendamentos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Botões de ação
        frame_acoes = ctk.CTkFrame(frame_lista, fg_color="transparent")
        frame_acoes.pack(fill="x", padx=10, pady=(0, 10))
        
        botoes = [
            ("✅ Confirmar", self.confirmar_agendamento),
            ("💰 Finalizar", self.finalizar_agendamento),
            ("❌ Cancelar", self.cancelar_agendamento),
            ("🗑️ Excluir", self.excluir_agendamento),
        ]
        
        for texto, comando in botoes:
            ctk.CTkButton(
                frame_acoes,
                text=texto,
                command=comando,
                width=120
            ).pack(side="left", padx=5)
        
        self.carregar_agendamentos_data()
    
    def carregar_agendamentos_data(self):
        for item in self.tree_agendamentos.get_children():
            self.tree_agendamentos.delete(item)
        
        data_str = self.data_selecionada.strftime("%Y-%m-%d")
        agendamentos = self.db.obter_agendamentos_do_dia(data_str)
        
        for ag in agendamentos:
            status_color = {
                'agendado': ('blue', 'Agendado'),
                'confirmado': ('green', 'Confirmado'),
                'finalizado': ('gray', 'Finalizado'),
                'cancelado': ('red', 'Cancelado')
            }.get(ag[7], ('black', ag[7]))
            
            self.tree_agendamentos.insert("", "end", values=(
                ag[4],
                ag[11],
                ag[12],
                ag[13],
                ag[6],
                f"R$ {ag[8]:.2f}",
                status_color[1]
            ), tags=(status_color[0],))
        
        for color in ['blue', 'green', 'gray', 'red']:
            self.tree_agendamentos.tag_configure(color, foreground=color)
    
    def mudar_data_agendamento(self, dias):
        self.data_selecionada += timedelta(days=dias)
        self.label_data_agendamento.configure(
            text=self.data_selecionada.strftime("%A, %d de %B de %Y").title()
        )
        self.carregar_agendamentos_data()
    
    def ir_para_hoje_agendamento(self):
        self.data_selecionada = datetime.now()
        self.label_data_agendamento.configure(
            text=self.data_selecionada.strftime("%A, %d de %B de %Y").title()
        )
        self.carregar_agendamentos_data()
    
    def abrir_novo_agendamento(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Novo Agendamento")
        janela.geometry("500x600")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(janela, text="Novo Agendamento", font=("Arial", 18, "bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(janela, fg_color="transparent")
        campos_frame.pack(padx=40, pady=10, fill="both")
        
        # Cliente
        ctk.CTkLabel(campos_frame, text="Cliente:").pack(anchor="w", pady=(0, 5))
        frame_cliente = ctk.CTkFrame(campos_frame, fg_color="transparent")
        frame_cliente.pack(fill="x", pady=(0, 10))
        
        self.entry_cliente_ag = ctk.CTkEntry(frame_cliente, width=200, placeholder_text="Nome do cliente")
        self.entry_cliente_ag.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_cliente,
            text="🔍 Buscar",
            command=self.buscar_cliente_agendamento,
            width=80
        ).pack(side="left")
        
        # Telefone
        ctk.CTkLabel(campos_frame, text="Telefone:").pack(anchor="w", pady=(0, 5))
        self.entry_telefone_ag = ctk.CTkEntry(campos_frame, width=200, placeholder_text="(11) 99999-9999")
        self.entry_telefone_ag.pack(anchor="w", pady=(0, 10))
        
        # Serviço
        ctk.CTkLabel(campos_frame, text="Serviço:").pack(anchor="w", pady=(0, 5))
        self.combo_servico_ag = ctk.CTkComboBox(
            campos_frame,
            width=300,
            values=self.obter_nomes_servicos()
        )
        self.combo_servico_ag.pack(anchor="w", pady=(0, 10))
        
        # Data
        ctk.CTkLabel(campos_frame, text="Data:").pack(anchor="w", pady=(0, 5))
        self.entry_data_ag = ctk.CTkEntry(campos_frame, width=150)
        self.entry_data_ag.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_data_ag.pack(anchor="w", pady=(0, 10))
        
        # Hora
        ctk.CTkLabel(campos_frame, text="Hora:").pack(anchor="w", pady=(0, 5))
        horas = [f"{h:02d}:00" for h in range(9, 19)] + [f"{h:02d}:30" for h in range(9, 19)]
        self.combo_hora_ag = ctk.CTkComboBox(campos_frame, width=100, values=horas)
        self.combo_hora_ag.set("09:00")
        self.combo_hora_ag.pack(anchor="w", pady=(0, 10))
        
        # Profissional
        ctk.CTkLabel(campos_frame, text="Profissional:").pack(anchor="w", pady=(0, 5))
        self.entry_profissional_ag = ctk.CTkEntry(campos_frame, width=200, placeholder_text="Nome do barbeiro")
        self.entry_profissional_ag.pack(anchor="w", pady=(0, 20))
        
        def criar():
            cliente = self.entry_cliente_ag.get().strip()
            telefone = self.entry_telefone_ag.get().strip()
            servico = self.combo_servico_ag.get()
            data = self.entry_data_ag.get().strip()
            hora = self.combo_hora_ag.get()
            profissional = self.entry_profissional_ag.get().strip()
            
            if not cliente or not telefone or not servico:
                CTkMessagebox(title="Erro", message="Preencha cliente, telefone e serviço!", icon="cancel")
                return
            
            try:
                data_obj = datetime.strptime(data, "%d/%m/%Y")
                data_banco = data_obj.strftime("%Y-%m-%d")
                
                servico_nome = servico.split(" - R$ ")[0]
                servico_valor = float(servico.split(" - R$ ")[1])
                
                cliente_existente = self.db.buscar_cliente_por_telefone(telefone)
                if cliente_existente:
                    cliente_id = cliente_existente[0]
                else:
                    cliente_id = self.db.adicionar_cliente(cliente, telefone)
                
                servicos = self.db.obter_servicos()
                servico_id = None
                for s in servicos:
                    if s[1] == servico_nome:
                        servico_id = s[0]
                        break
                
                if not servico_id:
                    CTkMessagebox(title="Erro", message="Serviço não encontrado!", icon="cancel")
                    return
                
                self.db.adicionar_agendamento(
                    cliente_id, servico_id, data_banco, hora,
                    profissional, servico_valor
                )
                
                CTkMessagebox(
                    title="Sucesso",
                    message=f"✅ Agendamento criado!\n\nCliente: {cliente}\nData: {data} {hora}\nServiço: {servico_nome}",
                    icon="check"
                )
                
                janela.destroy()
                self.carregar_agendamentos_data()
                
            except ValueError:
                CTkMessagebox(title="Erro", message="Data inválida! Use DD/MM/AAAA", icon="cancel")
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro: {str(e)}", icon="cancel")
        
        ctk.CTkButton(
            janela,
            text="📅 Criar Agendamento",
            command=criar,
            fg_color="#4CAF50",
            width=200,
            height=40
        ).pack(pady=20)
    
    def buscar_cliente_agendamento(self):
        telefone = self.entry_telefone_ag.get().strip()
        if telefone:
            cliente = self.db.buscar_cliente_por_telefone(telefone)
            if cliente:
                self.entry_cliente_ag.delete(0, "end")
                self.entry_cliente_ag.insert(0, cliente[1])
                CTkMessagebox(title="Sucesso", message=f"Cliente encontrado: {cliente[1]}", icon="info")
            else:
                CTkMessagebox(title="Aviso", message="Cliente não encontrado. Cadastre um novo.", icon="warning")
    
    def obter_nomes_servicos(self):
        servicos = self.db.obter_servicos()
        return [f"{s[1]} - R$ {s[2]:.2f}" for s in servicos]
    
    def confirmar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        valores = item['values']
        
        resposta = CTkMessagebox(
            title="Confirmar Agendamento",
            message=f"Confirmar agendamento de {valores[1]} para {valores[3]}?",
            icon="question",
            option_1="Cancelar",
            option_2="Confirmar"
        )
        
        if resposta.get() == "Confirmar":
            data_str = self.data_selecionada.strftime("%Y-%m-%d")
            self.db.cursor.execute('''
                SELECT a.id 
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                JOIN servicos s ON a.servico_id = s.id
                WHERE a.data = ? AND a.hora = ? AND c.nome = ? AND s.nome = ?
            ''', (data_str, valores[0], valores[1], valores[3]))
            
            resultado = self.db.cursor.fetchone()
            if resultado:
                self.db.atualizar_status_agendamento(resultado[0], 'confirmado')
                self.carregar_agendamentos_data()
                CTkMessagebox(title="Sucesso", message="Agendamento confirmado!", icon="check")
    
    def finalizar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        valores = item['values']
        
        resposta = CTkMessagebox(
            title="Finalizar Agendamento",
            message=f"Finalizar agendamento de {valores[1]}?",
            icon="question",
            option_1="Cancelar",
            option_2="Finalizar"
        )
        
        if resposta.get() == "Finalizar":
            data_str = self.data_selecionada.strftime("%Y-%m-%d")
            self.db.cursor.execute('''
                SELECT a.id 
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                JOIN servicos s ON a.servico_id = s.id
                WHERE a.data = ? AND a.hora = ? AND c.nome = ? AND s.nome = ?
            ''', (data_str, valores[0], valores[1], valores[3]))
            
            resultado = self.db.cursor.fetchone()
            if resultado:
                self.db.atualizar_status_agendamento(resultado[0], 'finalizado')
                self.carregar_agendamentos_data()
                CTkMessagebox(title="Sucesso", message="Agendamento finalizado!", icon="check")
    
    def cancelar_agendamento(self):
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        valores = item['values']
        
        resposta = CTkMessagebox(
            title="Cancelar Agendamento",
            message=f"Cancelar agendamento de {valores[1]}?",
            icon="warning",
            option_1="Cancelar",
            option_2="Confirmar"
        )
        
        if resposta.get() == "Confirmar":
            data_str = self.data_selecionada.strftime("%Y-%m-%d")
            self.db.cursor.execute('''
                SELECT a.id 
                FROM agendamentos a
                JOIN clientes c ON a.cliente_id = c.id
                JOIN servicos s ON a.servico_id = s.id
                WHERE a.data = ? AND a.hora = ? AND c.nome = ? AND s.nome = ?
            ''', (data_str, valores[0], valores[1], valores[3]))
            
            resultado = self.db.cursor.fetchone()
            if resultado:
                self.db.atualizar_status_agendamento(resultado[0], 'cancelado')
                self.carregar_agendamentos_data()
                CTkMessagebox(title="Sucesso", message="Agendamento cancelado!", icon="check")
    
    def excluir_agendamento(self):
        """EXCLUI agendamento do banco de dados - CORRIGIDO"""
        selecionado = self.tree_agendamentos.selection()
        if not selecionado:
            CTkMessagebox(title="Aviso", message="Selecione um agendamento!", icon="warning")
            return
        
        item = self.tree_agendamentos.item(selecionado[0])
        valores = item['values']
        
        hora = valores[0]
        cliente = valores[1]
        servico = valores[3]
        
        resposta = CTkMessagebox(
            title="Confirmar Exclusão",
            message=f"EXCLUIR agendamento?\n\n👤 {cliente}\n✂️ {servico}\n⏰ {hora}",
            icon="warning",
            option_1="Cancelar",
            option_2="Excluir"
        )
        
        if resposta.get() == "Excluir":
            try:
                data_str = self.data_selecionada.strftime("%Y-%m-%d")
                
                self.db.cursor.execute('''
                    SELECT a.id 
                    FROM agendamentos a
                    JOIN clientes c ON a.cliente_id = c.id
                    JOIN servicos s ON a.servico_id = s.id
                    WHERE a.data = ? AND a.hora = ? AND c.nome = ? AND s.nome = ?
                ''', (data_str, hora, cliente, servico))
                
                resultado = self.db.cursor.fetchone()
                
                if resultado:
                    agendamento_id = resultado[0]
                    self.db.excluir_agendamento(agendamento_id)
                    
                    CTkMessagebox(
                        title="✅ Excluído!",
                        message=f"Agendamento excluído com sucesso.",
                        icon="check"
                    )
                    
                    self.carregar_agendamentos_data()
                else:
                    CTkMessagebox(title="Erro", message="Agendamento não encontrado!", icon="cancel")
                    
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao excluir: {str(e)}", icon="cancel")
    
    # =============================================================
    # 6. CAIXA COMPLETO COM FECHAMENTO FUNCIONAL
    # =============================================================
    def mostrar_caixa(self):
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="💰 Controle de Caixa",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        caixa_aberto = self.db.caixa_esta_aberto()
        
        if caixa_aberto:
            self.mostrar_caixa_aberto()
        else:
            self.mostrar_caixa_fechado()
    
    def mostrar_caixa_aberto(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="✅ Caixa Aberto",
            font=("Arial", 20, "bold"),
            text_color="#4CAF50"
        ).pack(pady=20)
        
        caixa = self.db.obter_caixa_hoje()
        if caixa:
            valor_inicial = caixa[2]
        else:
            valor_inicial = 0
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        total_vendas = self.db.obter_total_vendas_periodo(hoje, hoje)
        total_esperado = valor_inicial + total_vendas
        
        metricas = [
            ("Valor Inicial", f"R$ {valor_inicial:,.2f}", "#2196F3"),
            ("Total em Vendas", f"R$ {total_vendas:,.2f}", "#4CAF50"),
            ("Total Esperado", f"R$ {total_esperado:,.2f}", "#FF9800"),
        ]
        
        for i, (titulo, valor, cor) in enumerate(metricas):
            card = ctk.CTkFrame(frame, fg_color=cor, corner_radius=10)
            card.grid(row=0, column=i, padx=20, pady=20, sticky="nsew")
            frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=titulo, font=("Arial", 14)).pack(pady=(15, 5))
            ctk.CTkLabel(card, text=valor, font=("Arial", 20, "bold")).pack(pady=(0, 15))
        
        ctk.CTkButton(
            frame,
            text="🔒 Fechar Caixa",
            command=self.fechar_caixa,
            fg_color="#D44336",
            height=50,
            font=("Arial", 16, "bold")
        ).pack(pady=40, padx=100, fill="x")
    
    def mostrar_caixa_fechado(self):
        frame = ctk.CTkFrame(self.frame_principal)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="🔒 Caixa Fechado",
            font=("Arial", 20, "bold"),
            text_color="#F44336"
        ).pack(pady=20)
        
        ctk.CTkLabel(frame, text="Valor Inicial do Caixa:", font=("Arial", 14)).pack(pady=(20, 10))
        
        self.entry_valor_inicial = ctk.CTkEntry(frame, width=200, placeholder_text="0.00")
        self.entry_valor_inicial.pack(pady=(0, 20))
        
        ctk.CTkButton(
            frame,
            text="🔓 Abrir Caixa",
            command=self.abrir_caixa,
            fg_color="#4CAF50",
            height=50,
            font=("Arial", 16, "bold")
        ).pack(pady=20, padx=100, fill="x")
    
    def abrir_caixa(self):
        try:
            valor_inicial = float(self.entry_valor_inicial.get().replace(',', '.'))
            self.db.abrir_caixa(valor_inicial)
            self.mostrar_caixa()
            CTkMessagebox(title="Sucesso", message="Caixa aberto com sucesso!", icon="check")
        except ValueError:
            CTkMessagebox(title="Erro", message="Valor inválido!", icon="cancel")
    
    def fechar_caixa(self):
        """FECHA o caixa corretamente - CORRIGIDO"""
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        resposta = CTkMessagebox(
            title="Fechar Caixa",
            message="Deseja fechar o caixa?\n\nIsso registrará o fechamento do dia.",
            icon="question",
            option_1="Cancelar",
            option_2="Fechar"
        )
        
        if resposta.get() == "Fechar":
            try:
                caixa = self.db.obter_caixa_hoje()
                if not caixa:
                    CTkMessagebox(title="Erro", message="Caixa não encontrado!", icon="cancel")
                    return
                
                valor_inicial = caixa[2]
                total_vendas = self.db.obter_total_vendas_periodo(hoje, hoje)
                valor_esperado = valor_inicial + total_vendas
                
                janela = ctk.CTkToplevel(self.janela)
                janela.title("Fechar Caixa")
                janela.geometry("400x300")
                janela.transient(self.janela)
                janela.grab_set()
                
                ctk.CTkLabel(
                    janela,
                    text="💰 Fechamento de Caixa",
                    font=("Arial", 18, "bold")
                ).pack(pady=20)
                
                info_text = f"""
                Valor Inicial: R$ {valor_inicial:.2f}
                Total em Vendas: R$ {total_vendas:.2f}
                Total Esperado: R$ {valor_esperado:.2f}
                """
                
                ctk.CTkLabel(janela, text=info_text, font=("Arial", 12)).pack(pady=10)
                
                ctk.CTkLabel(janela, text="Valor Físico no Caixa:").pack(pady=(20, 5))
                entry_valor_fisico = ctk.CTkEntry(janela, width=200)
                entry_valor_fisico.insert(0, f"{valor_esperado:.2f}")
                entry_valor_fisico.pack(pady=(0, 20))
                
                def confirmar_fechamento():
                    try:
                        valor_fisico = float(entry_valor_fisico.get().replace(',', '.'))
                        
                        self.db.fechar_caixa(valor_fisico)
                        
                        diferenca = valor_fisico - valor_esperado
                        
                        mensagem = f"""
                        ✅ Caixa fechado com sucesso!
                        
                        📊 Resumo:
                        • Valor Inicial: R$ {valor_inicial:.2f}
                        • Total em Vendas: R$ {total_vendas:.2f}
                        • Total Esperado: R$ {valor_esperado:.2f}
                        • Valor Físico: R$ {valor_fisico:.2f}
                        • Diferença: R$ {diferenca:.2f} {'(Sobra)' if diferenca >= 0 else '(Falta)'}
                        """
                        
                        janela.destroy()
                        CTkMessagebox(title="Caixa Fechado", message=mensagem, icon="check")
                        self.mostrar_caixa()
                        
                    except ValueError:
                        CTkMessagebox(title="Erro", message="Valor inválido!", icon="cancel")
                
                ctk.CTkButton(
                    janela,
                    text="🔒 Confirmar Fechamento",
                    command=confirmar_fechamento,
                    fg_color="#4CAF50",
                    width=200
                ).pack(pady=20)
                
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao fechar caixa: {str(e)}", icon="cancel")
    
    # =============================================================
    # 7. NOVA VENDA COMPLETO E FUNCIONAL - CORRIGIDO
    # =============================================================
    def mostrar_nova_venda(self):
        """Módulo para iniciar serviço/vender produto"""
        self.limpar_frame_principal()
        
        ctk.CTkLabel(
            self.frame_principal,
            text="Nova Venda / Iniciar Serviço",
            font=("Arial", 24, "bold")
        ).pack(pady=20)
        
        # Frame principal com duas colunas
        frame_principal = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        frame_principal.grid_columnconfigure(0, weight=1)
        frame_principal.grid_columnconfigure(1, weight=1)
        frame_principal.grid_rowconfigure(0, weight=1)
        
        # Coluna 1: Seleção de Cliente e Itens
        frame_esquerda = ctk.CTkFrame(frame_principal)
        frame_esquerda.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        
        # Cliente
        ctk.CTkLabel(
            frame_esquerda,
            text="👤 Cliente",
            font=("Arial", 16, "bold")
        ).pack(pady=(15, 10))
        
        # Buscar cliente por telefone
        frame_busca = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        frame_busca.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(frame_busca, text="Telefone:").pack(side="left", padx=(0, 10))
        self.entry_telefone_cliente = ctk.CTkEntry(frame_busca, width=150)
        self.entry_telefone_cliente.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_busca,
            text="🔍 Buscar",
            command=self.buscar_cliente_venda,
            width=80
        ).pack(side="left")
        
        # Informações do cliente
        self.frame_info_cliente = ctk.CTkFrame(frame_esquerda, fg_color="#1E3A5F")
        self.frame_info_cliente.pack(fill="x", padx=20, pady=(0, 20))
        self.label_info_cliente = ctk.CTkLabel(
            self.frame_info_cliente,
            text="Digite um telefone e clique em Buscar",
            font=("Arial", 12)
        )
        self.label_info_cliente.pack(pady=10)
        
        # Seleção de tipo
        ctk.CTkLabel(
            frame_esquerda,
            text="📦Selecionar Item",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))
        
        self.tipo_venda = ctk.StringVar(value="servico")
        
        frame_tipo = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        frame_tipo.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkRadioButton(
            frame_tipo,
            text="✂️ Serviço",
            variable=self.tipo_venda,
            value="servico",
            command=self.atualizar_lista_itens_venda
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkRadioButton(
            frame_tipo,
            text="🛍️ Produto",
            variable=self.tipo_venda,
            value="produto",
            command=self.atualizar_lista_itens_venda
        ).pack(side="left")
        
        # Lista de itens
        self.frame_lista_itens = ctk.CTkFrame(frame_esquerda)
        self.frame_lista_itens.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Quantidade (apenas para produtos)
        self.frame_quantidade = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        self.frame_quantidade.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(self.frame_quantidade, text="Quantidade:").pack(side="left", padx=(0, 10))
        self.entry_quantidade = ctk.CTkEntry(self.frame_quantidade, width=80)
        self.entry_quantidade.insert(0, "1")
        self.entry_quantidade.pack(side="left")
        
        # Coluna 2: Resumo e Pagamento
        frame_direita = ctk.CTkFrame(frame_principal)
        frame_direita.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            frame_direita,
            text="Resumo da Venda",
            font=("Arial", 16, "bold")
        ).pack(pady=(15, 10))
        
        # Lista de itens selecionados
        self.frame_itens_selecionados = ctk.CTkScrollableFrame(frame_direita, height=200)
        self.frame_itens_selecionados.pack(fill="x", padx=20, pady=(0, 10))
        
        # Total
        self.frame_total = ctk.CTkFrame(frame_direita, fg_color="#2196F3")
        self.frame_total.pack(fill="x", padx=20, pady=10)
        
        self.label_total = ctk.CTkLabel(
            self.frame_total,
            text="Total: R$ 0,00",
            font=("Arial", 18, "bold")
        )
        self.label_total.pack(pady=10)
        
        # Forma de pagamento
        ctk.CTkLabel(
            frame_direita,
            text="Forma de Pagamento",
            font=("Arial", 14)
        ).pack(pady=(10, 5))
        
        self.forma_pagamento = ctk.StringVar(value="Dinheiro")
        formas = ["Dinheiro", "Cartão Débito", "Cartão Crédito", "PIX", "Transferência"]
        
        for forma in formas:
            ctk.CTkRadioButton(
                frame_direita,
                text=forma,
                variable=self.forma_pagamento,
                value=forma
            ).pack(anchor="w", padx=50, pady=2)
        
        # Botão finalizar
        ctk.CTkButton(
            frame_direita,
            text="💳 Finalizar Venda",
            command=self.finalizar_venda,
            fg_color="#4CAF50",
            height=50,
            font=("Arial", 16, "bold")
        ).pack(pady=30, padx=50, fill="x")
        
        # Inicializar lista de itens
        self.itens_selecionados = []
        self.cliente_venda_id = None
        self.atualizar_lista_itens_venda()
    
    def buscar_cliente_venda(self):
        """Busca cliente por telefone"""
        telefone = self.entry_telefone_cliente.get().strip()
        
        if not telefone:
            CTkMessagebox(title="Aviso", message="Digite um telefone!", icon="warning")
            return
        
        cliente = self.db.buscar_cliente_por_telefone(telefone)
        
        if cliente:
            self.cliente_venda_id = cliente[0]
            self.label_info_cliente.configure(
                text=f"✅ Cliente encontrado:\n{cliente[1]}\nTelefone: {cliente[2]}\nTotal Gasto: R$ {cliente[6]:.2f}\nVisitas: {cliente[7]}"
            )
            self.frame_info_cliente.configure(fg_color="#E8F5E9")
        else:
            self.cliente_venda_id = None
            self.label_info_cliente.configure(
                text=f"❌ Cliente não encontrado\nTelefone: {telefone}\n\nDeseja cadastrar novo cliente?"
            )
            self.frame_info_cliente.configure(fg_color="#FFEBEE")
            
            # Botão para cadastrar novo cliente
            for widget in self.frame_info_cliente.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.destroy()
            
            ctk.CTkButton(
                self.frame_info_cliente,
                text="➕ Cadastrar Novo Cliente",
                command=self.cadastrar_cliente_rapido,
                height=30
            ).pack(pady=(0, 10))
    
    def cadastrar_cliente_rapido(self):
        """Cadastra cliente rapidamente durante a venda"""
        telefone = self.entry_telefone_cliente.get().strip()
        
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Cadastrar Cliente Rápido")
        janela.geometry("400x300")
        janela.transient(self.janela)
        janela.grab_set()
        
        ctk.CTkLabel(
            janela,
            text="Cadastrar Cliente",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        frame_campos = ctk.CTkFrame(janela, fg_color="transparent")
        frame_campos.pack(padx=40, pady=10, fill="both")
        
        ctk.CTkLabel(frame_campos, text="Nome:").pack(anchor="w", pady=(0, 5))
        entry_nome = ctk.CTkEntry(frame_campos, width=300)
        entry_nome.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(frame_campos, text="Telefone:").pack(anchor="w", pady=(0, 5))
        entry_telefone = ctk.CTkEntry(frame_campos, width=200)
        entry_telefone.insert(0, telefone)
        entry_telefone.pack(anchor="w", pady=(0, 15))
        
        def cadastrar():
            nome = entry_nome.get().strip()
            telefone = entry_telefone.get().strip()
            
            if not nome or not telefone:
                CTkMessagebox(title="Erro", message="Preencha nome e telefone!", icon="cancel")
                return
            
            try:
                cliente_id = self.db.adicionar_cliente(nome, telefone)
                self.cliente_venda_id = cliente_id
                janela.destroy()
                self.buscar_cliente_venda()  # Atualizar display
                CTkMessagebox(title="Sucesso", message="Cliente cadastrado!", icon="check")
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao cadastrar: {str(e)}", icon="cancel")
        
        ctk.CTkButton(
            janela,
            text="💾 Cadastrar",
            command=cadastrar,
            width=200
        ).pack(pady=20)
    
    def atualizar_lista_itens_venda(self):
        """Atualiza a lista de itens (serviços ou produtos)"""
        # Limpar frame
        for widget in self.frame_lista_itens.winfo_children():
            widget.destroy()
        
        tipo = self.tipo_venda.get()
        
        if tipo == "servico":
            itens = self.db.obter_servicos()
            for servico in itens:
                btn = ctk.CTkButton(
                    self.frame_lista_itens,
                    text=f"{servico[1]} - R$ {servico[2]:.2f} ({servico[3]} min)",
                    command=lambda s=servico: self.adicionar_item_venda(s, "servico"),
                    anchor="w",
                    fg_color="transparent",
                    hover_color="#2B2B2B",
                    height=40
                )
                btn.pack(fill="x", pady=2)
        else:
            itens = self.db.obter_produtos()
            for produto in itens:
                btn = ctk.CTkButton(
                    self.frame_lista_itens,
                    text=f"{produto[1]} - R$ {produto[2]:.2f} (Estoque: {produto[4]})",
                    command=lambda p=produto: self.adicionar_item_venda(p, "produto"),
                    anchor="w",
                    fg_color="transparent",
                    hover_color="#2B2B2B",
                    height=40
                )
                btn.pack(fill="x", pady=2)
        
        # Mostrar/ocultar quantidade
        if tipo == "produto":
            self.frame_quantidade.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.frame_quantidade.pack_forget()
    
    def adicionar_item_venda(self, item, tipo):
        """Adiciona item à lista de vendas"""
        try:
            quantidade = 1
            if tipo == "produto":
                quantidade = int(self.entry_quantidade.get())
                if quantidade <= 0:
                    CTkMessagebox(title="Erro", message="Quantidade deve ser maior que zero!", icon="cancel")
                    return
                
                # Verificar estoque
                if quantidade > item[4]:
                    CTkMessagebox(title="Erro", message=f"Estoque insuficiente! Disponível: {item[4]}", icon="cancel")
                    return
            
            valor_unitario = item[2] if tipo == "servico" else item[2]  # item[2] é valor_venda para produtos
            valor_total = valor_unitario * quantidade
            
            # Adicionar à lista
            self.itens_selecionados.append({
                'id': item[0],
                'nome': item[1],
                'tipo': tipo,
                'quantidade': quantidade,
                'valor_unitario': valor_unitario,
                'valor_total': valor_total
            })
            
            self.atualizar_resumo_venda()
            
        except ValueError:
            CTkMessagebox(title="Erro", message="Quantidade inválida!", icon="cancel")
    
    def atualizar_resumo_venda(self):
        """Atualiza o resumo da venda"""
        # Limpar frame
        for widget in self.frame_itens_selecionados.winfo_children():
            widget.destroy()
        
        total = 0
        
        for i, item in enumerate(self.itens_selecionados):
            frame_item = ctk.CTkFrame(self.frame_itens_selecionados, fg_color="#2B2B2B")
            frame_item.pack(fill="x", pady=2, padx=2)
            
            # Nome e valor
            info_text = f"{item['nome']} - {item['quantidade']}x R$ {item['valor_unitario']:.2f} = R$ {item['valor_total']:.2f}"
            ctk.CTkLabel(
                frame_item,
                text=info_text,
                font=("Arial", 11)
            ).pack(side="left", padx=10, pady=5)
            
            # Botão remover
            ctk.CTkButton(
                frame_item,
                text="❌",
                width=30,
                height=30,
                command=lambda idx=i: self.remover_item_venda(idx)
            ).pack(side="right", padx=5)
            
            total += item['valor_total']
        
        # Atualizar total
        self.label_total.configure(text=f"Total: R$ {total:.2f}")
    
    def remover_item_venda(self, index):
        """Remove item da lista de vendas"""
        if 0 <= index < len(self.itens_selecionados):
            self.itens_selecionados.pop(index)
            self.atualizar_resumo_venda()
    
    def finalizar_venda(self):
        """Finaliza a venda"""
        if not self.itens_selecionados:
            CTkMessagebox(title="Aviso", message="Adicione itens à venda!", icon="warning")
            return
        
        if not self.cliente_venda_id:
            resposta = CTkMessagebox(
                title="Cliente não identificado",
                message="Deseja continuar a venda sem cliente?",
                icon="question",
                option_1="Cancelar",
                option_2="Continuar"
            )
            
            if resposta.get() == "Cancelar":
                return
        
        # Calcular total
        total = sum(item['valor_total'] for item in self.itens_selecionados)
        
        # Confirmar venda
        resposta = CTkMessagebox(
            title="Confirmar Venda",
            message=f"Total: R$ {total:.2f}\n\nDeseja finalizar a venda?",
            icon="question",
            option_1="Cancelar",
            option_2="Finalizar"
        )
        
        if resposta.get() == "Finalizar":
            try:
                # Registrar cada item
                for item in self.itens_selecionados:
                    self.db.registrar_venda(
                        self.cliente_venda_id,
                        item['tipo'],
                        item['id'],
                        item['quantidade'],
                        item['valor_unitario'],
                        self.forma_pagamento.get()
                    )
                
                # Limpar tudo
                self.itens_selecionados = []
                self.entry_telefone_cliente.delete(0, "end")
                self.cliente_venda_id = None
                self.label_info_cliente.configure(text="Digite um telefone e clique em Buscar")
                self.frame_info_cliente.configure(fg_color="#E8F5E9")
                self.atualizar_resumo_venda()
                
                # Mostrar recibo
                CTkMessagebox(
                    title="Venda Concluída!",
                    message=f"✅ Venda registrada com sucesso!\n\nTotal: R$ {total:.2f}\nForma de pagamento: {self.forma_pagamento.get()}",
                    icon="check"
                )
                
            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Erro ao registrar venda: {str(e)}", icon="cancel")
    
    # =============================================================
    # 8. RELATÓRIOS COMPLETO COM BOTÃO BAIXAR - CORRIGIDO
    # =============================================================
    def mostrar_relatorios(self):
        self.limpar_frame_principal()
        
        notebook = ctk.CTkTabview(self.frame_principal)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        notebook.add("Financeiro")
        notebook.add("Vendas")
        notebook.add("Clientes")
        notebook.add("Serviços")
        notebook.add("Produtos")
        
        self.criar_relatorio_financeiro(notebook.tab("Financeiro"))
        self.criar_relatorio_vendas(notebook.tab("Vendas"))
        self.criar_relatorio_clientes(notebook.tab("Clientes"))
        self.criar_relatorio_servicos(notebook.tab("Serviços"))
        self.criar_relatorio_produtos(notebook.tab("Produtos"))
    
    def criar_relatorio_financeiro(self, frame):
        ctk.CTkLabel(frame, text="📊 Relatório Financeiro", font=("Arial", 18, "bold")).pack(pady=20)
        
        frame_superior = ctk.CTkFrame(frame, fg_color="transparent")
        frame_superior.pack(fill="x", padx=20, pady=(0, 10))
        
        frame_periodo = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_periodo.pack(side="left", fill="y")
        
        hoje = datetime.now()
        primeiro_dia_mes = hoje.replace(day=1).strftime("%Y-%m-%d")
        hoje_str = hoje.strftime("%Y-%m-%d")
        
        ctk.CTkLabel(frame_periodo, text="De:").pack(side="left", padx=(0, 10))
        self.entry_rel_inicio = ctk.CTkEntry(frame_periodo, width=120)
        self.entry_rel_inicio.insert(0, primeiro_dia_mes)
        self.entry_rel_inicio.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(frame_periodo, text="Até:").pack(side="left", padx=(0, 10))
        self.entry_rel_fim = ctk.CTkEntry(frame_periodo, width=120)
        self.entry_rel_fim.insert(0, hoje_str)
        self.entry_rel_fim.pack(side="left", padx=(0, 20))
        
        frame_botoes = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_botoes.pack(side="right")
        
        ctk.CTkButton(
            frame_botoes,
            text="🔍 Gerar Relatório",
            command=self.gerar_relatorio_financeiro,
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            frame_botoes,
            text="📥 Baixar Excel",
            command=self.baixar_relatorio_excel,
            fg_color="#4CAF50",
            width=150
        ).pack(side="left")
        
        self.frame_resultados_rel = ctk.CTkFrame(frame)
        self.frame_resultados_rel.pack(fill="both", expand=True, padx=20, pady=20)
    
    def gerar_relatorio_financeiro(self):
        data_inicio = self.entry_rel_inicio.get()
        data_fim = self.entry_rel_fim.get()
        
        try:
            resumo = self.db.obter_resumo_financeiro(data_inicio, data_fim)
            
            for widget in self.frame_resultados_rel.winfo_children():
                widget.destroy()
            
            metricas = [
                ("💰 Total em Vendas", f"R$ {resumo['total_vendas']:,.2f}", "#4CAF50"),
                ("💸 Total em Despesas", f"R$ {resumo['total_despesas']:,.2f}", "#F44336"),
                ("📈 Lucro Líquido", f"R$ {resumo['lucro']:,.2f}", "#4CAF50" if resumo['lucro'] >= 0 else "#F44336"),
            ]
            
            for titulo, valor, cor in metricas:
                linha = ctk.CTkFrame(self.frame_resultados_rel, fg_color=cor, corner_radius=8)
                linha.pack(fill="x", padx=50, pady=5)
                
                ctk.CTkLabel(linha, text=titulo, font=("Arial", 14)).pack(side="left", padx=20, pady=10)
                ctk.CTkLabel(linha, text=valor, font=("Arial", 16, "bold")).pack(side="right", padx=20, pady=10)
            
            if resumo['total_vendas'] > 0:
                margem = (resumo['lucro'] / resumo['total_vendas']) * 100
                linha_margem = ctk.CTkFrame(self.frame_resultados_rel)
                linha_margem.pack(fill="x", padx=50, pady=10)
                
                ctk.CTkLabel(
                    linha_margem,
                    text=f"📊 Margem de Lucro: {margem:.1f}%",
                    font=("Arial", 14),
                    text_color="#4CAF50" if margem >= 0 else "#F44336"
                ).pack()
            
            ctk.CTkButton(
                self.frame_resultados_rel,
                text="📥 Baixar Relatório Detalhado",
                command=lambda: self.baixar_relatorio_excel(data_inicio, data_fim),
                fg_color="#2196F3",
                width=250,
                height=40
            ).pack(pady=20)
            
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro: {str(e)}", icon="cancel")
    
    def baixar_relatorio_excel(self, data_inicio=None, data_fim=None):
        if not data_inicio:
            data_inicio = self.entry_rel_inicio.get()
        if not data_fim:
            data_fim = self.entry_rel_fim.get()
        
        try:
            vendas = self.db.obter_vendas_periodo(data_inicio, data_fim)
            despesas = self.db.obter_despesas_periodo(data_inicio, data_fim)
            
            if not vendas and not despesas:
                CTkMessagebox(title="Aviso", message="Nenhum dado encontrado para o período!", icon="warning")
                return
            
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"relatorio_{data_inicio}_{data_fim}.xlsx"
            )
            
            if not arquivo:
                return
            
            with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
                if vendas:
                    df_vendas = pd.DataFrame(vendas, columns=[
                        'ID', 'Cliente_ID', 'Tipo', 'Item_ID', 'Quantidade', 
                        'Valor_Unitario', 'Valor_Total', 'Forma_Pagamento', 'Data', 'Item_Nome', 'Cliente_Nome'
                    ])
                    df_vendas.to_excel(writer, sheet_name='Vendas', index=False)
                
                if despesas:
                    df_despesas = pd.DataFrame(despesas, columns=[
                        'ID', 'Descricao', 'Categoria', 'Valor', 'Data', 'Forma_Pagamento', 'Observacoes'
                    ])
                    df_despesas.to_excel(writer, sheet_name='Despesas', index=False)
                
                resumo = self.db.obter_resumo_financeiro(data_inicio, data_fim)
                df_resumo = pd.DataFrame([resumo])
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            CTkMessagebox(
                title="✅ Relatório Baixado!",
                message=f"Relatório salvo em:\n{arquivo}",
                icon="check"
            )
            
        except ImportError:
            CTkMessagebox(
                title="Erro",
                message="Instale pandas e openpyxl:\npip install pandas openpyxl",
                icon="cancel"
            )
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro ao salvar: {str(e)}", icon="cancel")
    
    def criar_relatorio_vendas(self, frame):
        ctk.CTkLabel(frame, text="📈 Relatório de Vendas", font=("Arial", 18, "bold")).pack(pady=20)
        
        frame_botoes = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkButton(
            frame_botoes,
            text="📥 Baixar Excel",
            command=lambda: self.baixar_relatorio_vendas_excel(),
            fg_color="#4CAF50",
            width=150
        ).pack(side="right")
        
        columns = ("Data", "Cliente", "Item", "Quantidade", "Valor", "Pagamento")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        vendas = self.db.obter_vendas_periodo(data_inicio, data_fim)
        for venda in vendas:
            tree.insert("", "end", values=(
                venda[8][:10] if len(venda) > 8 and venda[8] else "",
                venda[9] or "Não informado",
                venda[8],
                venda[4],
                f"R$ {venda[6]:.2f}",
                venda[7]
            ))
    
    def baixar_relatorio_vendas_excel(self):
        try:
            data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            data_fim = datetime.now().strftime("%Y-%m-%d")
            
            vendas = self.db.obter_vendas_periodo(data_inicio, data_fim)
            
            if not vendas:
                CTkMessagebox(title="Aviso", message="Nenhuma venda encontrada!", icon="warning")
                return
            
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"relatorio_vendas_{data_inicio}_{data_fim}.xlsx"
            )
            
            if not arquivo:
                return
            
            df_vendas = pd.DataFrame(vendas, columns=[
                'ID', 'Cliente_ID', 'Tipo', 'Item_ID', 'Quantidade', 
                'Valor_Unitario', 'Valor_Total', 'Forma_Pagamento', 'Data', 'Item_Nome', 'Cliente_Nome'
            ])
            
            df_vendas.to_excel(arquivo, index=False)
            
            CTkMessagebox(
                title="✅ Relatório Baixado!",
                message=f"Relatório de vendas salvo em:\n{arquivo}",
                icon="check"
            )
            
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro ao salvar: {str(e)}", icon="cancel")
    
    def criar_relatorio_clientes(self, frame):
        ctk.CTkLabel(frame, text="👥 Relatório de Clientes", font=("Arial", 18, "bold")).pack(pady=20)
        
        columns = ("Nome", "Telefone", "Total Gasto", "Visitas", "Média/Visita")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        clientes = self.db.obter_top_clientes(20)
        for cliente in clientes:
            media = cliente[1] / cliente[2] if cliente[2] > 0 else 0
            tree.insert("", "end", values=(
                cliente[0],
                "",
                f"R$ {cliente[1]:,.2f}",
                cliente[2],
                f"R$ {media:.2f}"
            ))
    
    def criar_relatorio_servicos(self, frame):
        ctk.CTkLabel(frame, text="✂️ Serviços Mais Vendidos", font=("Arial", 18, "bold")).pack(pady=20)
        
        columns = ("Serviço", "Quantidade", "Faturamento", "Média")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        servicos = self.db.obter_servicos_mais_vendidos(data_inicio, data_fim)
        for servico in servicos:
            media = servico[2] / servico[1] if servico[1] > 0 else 0
            tree.insert("", "end", values=(
                servico[0],
                servico[1],
                f"R$ {servico[2]:,.2f}",
                f"R$ {media:.2f}"
            ))
    
    def criar_relatorio_produtos(self, frame):
        ctk.CTkLabel(frame, text="🛍️ Produtos Mais Vendidos", font=("Arial", 18, "bold")).pack(pady=20)
        
        columns = ("Produto", "Quantidade", "Faturamento", "Média")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        
        produtos = self.db.obter_produtos_mais_vendidos(data_inicio, data_fim)
        for produto in produtos:
            media = produto[2] / produto[1] if produto[1] > 0 else 0
            tree.insert("", "end", values=(
                produto[0],
                produto[1],
                f"R$ {produto[2]:,.2f}",
                f"R$ {media:.2f}"
            ))
    
    # =============================================================
    # 9. CONFIGURAÇÕES
    # =============================================================
    def mostrar_configuracoes(self):
        self.limpar_frame_principal()
        
        notebook = ctk.CTkTabview(self.frame_principal)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        notebook.add("Empresa")
        notebook.add("Horários")
        notebook.add("Backup")
        notebook.add("Sistema")
        
        self.criar_config_empresa(notebook.tab("Empresa"))
        self.criar_config_horarios(notebook.tab("Horários"))
        self.criar_config_backup(notebook.tab("Backup"))
        self.criar_config_sistema(notebook.tab("Sistema"))
    
    def criar_config_empresa(self, frame):
        ctk.CTkLabel(frame, text="Configurações da Empresa", font=("Arial", 18, "bold")).pack(pady=20)
        
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
            command=lambda: CTkMessagebox(title="Sucesso", message="Configurações salvas!", icon="check"),
            width=200
        ).pack(pady=30)
    
    def criar_config_horarios(self, frame):
        ctk.CTkLabel(frame, text="Horários de Funcionamento", font=("Arial", 18, "bold")).pack(pady=20)
        
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
            
            var_aberto = ctk.BooleanVar(value=aberto)
            ctk.CTkCheckBox(
                linha,
                text=dia,
                variable=var_aberto,
                width=150
            ).pack(side="left")
            
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
            command=lambda: CTkMessagebox(title="Sucesso", message="Horários salvos!", icon="check"),
            width=200
        ).pack(pady=30)
    
    def criar_config_backup(self, frame):
        ctk.CTkLabel(frame, text="Backup do Sistema", font=("Arial", 18, "bold")).pack(pady=20)
        
        info_frame = ctk.CTkFrame(frame, fg_color="#E3F2FD")
        info_frame.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="⚠️ Faça backup regularmente para não perder dados!",
            font=("Arial", 12),
            text_color="#1565C0"
        ).pack(pady=10)
        
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
            command=lambda: CTkMessagebox(title="Info", message="Funcionalidade em desenvolvimento", icon="info"),
            width=200
        ).pack(pady=10)
    
    def fazer_backup(self):
        try:
            pasta = Path("backups")
            pasta.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = pasta / f"backup_{timestamp}.db"
            
            shutil.copy2("barbearia.db", arquivo)
            
            CTkMessagebox(
                title="Backup Concluído",
                message=f"Backup criado!\n\nArquivo: {arquivo.name}",
                icon="check"
            )
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro: {str(e)}", icon="cancel")
    
    def criar_config_sistema(self, frame):
        ctk.CTkLabel(frame, text="Configurações do Sistema", font=("Arial", 18, "bold")).pack(pady=20)
        
        ctk.CTkLabel(frame, text="Tema:", font=("Arial", 14)).pack(anchor="w", padx=50, pady=(10, 5))
        
        var_tema = ctk.StringVar(value="dark")
        frame_tema = ctk.CTkFrame(frame, fg_color="transparent")
        frame_tema.pack(anchor="w", padx=50, pady=(0, 20))
        
        ctk.CTkRadioButton(frame_tema, text="🌙 Escuro", variable=var_tema, value="dark").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(frame_tema, text="☀️ Claro", variable=var_tema, value="light").pack(side="left")
        
        def aplicar_tema():
            ctk.set_appearance_mode(var_tema.get())
            CTkMessagebox(title="Sucesso", message="Tema aplicado!", icon="check")
        
        ctk.CTkButton(
            frame,
            text="💾 Aplicar Configurações",
            command=aplicar_tema,
            width=200
        ).pack(pady=30)
    
    # =============================================================
    # FUNÇÕES AUXILIARES
    # =============================================================
    def confirmar_agendamento_dash(self):
        CTkMessagebox(title="Info", message="Funcionalidade em desenvolvimento", icon="info")
    
    def finalizar_agendamento_dash(self):
        CTkMessagebox(title="Info", message="Funcionalidade em desenvolvimento", icon="info")
    
    def cancelar_agendamento_dash(self):
        CTkMessagebox(title="Info", message="Funcionalidade em desenvolvimento", icon="info")
    
    def limpar_frame_principal(self):
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
    
    def sair(self):
        resposta = CTkMessagebox(
            title="Sair",
            message="Deseja realmente sair?",
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
# EXECUÇÃO
# =============================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    login = LoginWindow()
    login.run()