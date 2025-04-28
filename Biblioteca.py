import sqlite3
from sqlite3 import Error
import datetime

class Biblioteca:
    def __init__(self):
        """Inicializa a conexão com o banco de dados SQLite e cria as tabelas"""
        try:
            self.connection = sqlite3.connect('biblioteca.db')
            self.cursor = self.connection.cursor()
            
            self._criar_tabelas()
            
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            exit()

    def _criar_tabelas(self):
        """Cria as tabelas necessárias no banco de dados"""
        scripts = [
            """CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                disponivel BOOLEAN DEFAULT TRUE
            )""",
            
            """CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                livro_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                data_emprestimo TEXT NOT NULL,
                data_devolucao TEXT NOT NULL,
                devolvido BOOLEAN DEFAULT FALSE,
                multa REAL DEFAULT 0.00,
                FOREIGN KEY (livro_id) REFERENCES livros(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )"""
        ]
        
        for script in scripts:
            try:
                self.cursor.execute(script)
                self.connection.commit()
            except Error as e:
                print(f"Erro ao criar tabelas: {e}")
                exit()
    def _criar_admin_se_necessario(self):
        try:
            self.cursor.execute("SELECT id FROM usuarios WHERE email = ?", ('admin@admin',))
            if not self.cursor.fetchone():
                self.cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                ('admin', 'admin@admin', '123')
        )
            self.connection.commit()
            print("Usuário admin criado com sucesso!")
        except Error as e:
            print(f"Erro ao verificar/criar usuário admin: {e}")
    
    def resetar_banco_de_dados(self):
        try:
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            self.cursor.execute("DELETE FROM emprestimos")
            self.cursor.execute("DELETE FROM livros")
            self.cursor.execute("DELETE FROM usuarios")
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self._criar_admin_se_necessario()
            self.connection.commit()
            print("Todos os dados foram resetados, mantendo a estrutura do banco.")
        except Error as e:
            print(f"Erro ao resetar o banco de dados: {e}")
            self.connection.rollback()

    # CADASTRO E CONSULTA
    def cadastrar_livro(self):
        """Cadastra um novo livro no sistema"""
        print("\n--- CADASTRO DE LIVRO ---")
        while True:
            titulo = input("Título do livro: ").strip()
            if not titulo:
                print("Erro: Título não pode ser vazio.")
                continue

            autor = input("Autor: ").strip()
            isbn = input("ISBN (13 dígitos): ").strip()
            
            if len(isbn) != 13 or not isbn.isdigit():
                print("Erro: ISBN inválido. Deve ter 13 dígitos.")
                continue

            try:
                self.cursor.execute(
                    "INSERT INTO livros (titulo, autor, isbn) VALUES (?, ?, ?)",
                    (titulo, autor, isbn)
                )
                self.connection.commit()
                print(f"Livro '{titulo}' cadastrado com sucesso! (ID: {self.cursor.lastrowid})")
                break
            except Error as e:
                print(f"Erro ao cadastrar livro: {e}")
                break

    def listar_livros(self):
        """Lista todos os livros cadastrados no sistema"""
        print("\n--- LIVROS CADASTRADOS ---")
        try:
            self.cursor.execute("SELECT * FROM livros")
            livros = self.cursor.fetchall()

            if not livros:
                print("Nenhum livro cadastrado.")
                return

            for livro in livros:
                status = "Disponível" if livro[4] else "Emprestado"
                print(f"ID: {livro[0]} | {livro[1]} ({livro[2]}) - ISBN: {livro[3]} | {status}")
        except Error as e:
            print(f"Erro ao listar livros: {e}")

    def buscar_livro(self):
        """Busca livros por título, autor ou ISBN"""
        print("\n--- BUSCAR LIVRO ---")
        termo = input("Digite título, autor ou ISBN: ").lower()
        
        try:
            self.cursor.execute("""
                SELECT * FROM livros 
                WHERE LOWER(titulo) LIKE ? 
                OR LOWER(autor) LIKE ? 
                OR isbn LIKE ?
            """, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))
            
            resultados = self.cursor.fetchall()

            if not resultados:
                print("Nenhum livro encontrado.")
            else:
                for livro in resultados:
                    status = "Disponível" if livro[4] else "Emprestado"
                    print(f"ID: {livro[0]} | {livro[1]} - {status}")
        except Error as e:
            print(f"Erro ao buscar livros: {e}")

    # USUÁRIOS
    def cadastrar_usuario(self):
        """Cadastra um novo usuário no sistema"""
        print("\n--- CADASTRO DE USUÁRIO ---")
        nome = input("Nome completo: ").strip()
        email = input("E-mail: ").strip()
        senha = input("Senha: ").strip()
        
        try:
            self.cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, senha)
            )
            self.connection.commit()
            print(f"Usuário '{nome}' cadastrado com sucesso! (ID: {self.cursor.lastrowid})")
        except Error as e:
            print(f"Erro ao cadastrar usuário: {e}")

    def listar_usuarios(self):
        """Lista todos os usuários cadastrados"""
        print("\n--- USUÁRIOS CADASTRADOS ---")
        try:
            self.cursor.execute("SELECT * FROM usuarios")
            usuarios = self.cursor.fetchall()

            if not usuarios:
                print("Nenhum usuário cadastrado.")
                return

            for usuario in usuarios:
                print(f"ID: {usuario[0]} | {usuario[1]} - {usuario[2]}")
        except Error as e:
            print(f"Erro ao listar usuários: {e}")

    # EMPRÉSTIMOS E DEVOLUÇÕES
    def emprestar_livro(self):
        """Registra o empréstimo de um livro"""
        print("\n--- EMPRÉSTIMO DE LIVRO ---")
        self.listar_livros()
        livro_id = input("ID do livro a emprestar: ")
        
        self.listar_usuarios()
        usuario_id = input("ID do usuário: ")

        try:
            # Verificar se o livro tá disponível
            self.cursor.execute("SELECT disponivel FROM livros WHERE id = ?", (livro_id,))
            livro = self.cursor.fetchone()
            
            if not livro:
                print("Erro: Livro não encontrado.")
                return
            if not livro[0]:
                print("Erro: Livro já emprestado.")
                return

            data_emprestimo = datetime.date.today().isoformat()
            data_devolucao = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()

            # Registrar o empréstimo
            self.cursor.execute("""
                INSERT INTO emprestimos 
                (livro_id, usuario_id, data_emprestimo, data_devolucao) 
                VALUES (?, ?, ?, ?)
            """, (livro_id, usuario_id, data_emprestimo, data_devolucao))
            
            # Atualizar o status do livro
            self.cursor.execute("UPDATE livros SET disponivel = 0 WHERE id = ?", (livro_id,))
            
            self.connection.commit()
            
            # Obter os detalhes pra exibição
            self.cursor.execute("SELECT titulo FROM livros WHERE id = ?", (livro_id,))
            titulo_livro = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT nome FROM usuarios WHERE id = ?", (usuario_id,))
            nome_usuario = self.cursor.fetchone()[0]
            
            print(f"Livro '{titulo_livro}' emprestado para {nome_usuario}. Devolução em {data_devolucao}.")
        except Error as e:
            print(f"Erro ao realizar empréstimo: {e}")

    def devolver_livro(self):
        """Registra a devolução de um livro"""
        print("\n--- DEVOLUÇÃO DE LIVRO ---")
        self.listar_emprestimos_ativos()
        emprestimo_id = input("ID do empréstimo a devolver: ")
        
        try:
            # Obter os dados do empréstimo
            self.cursor.execute("""
                SELECT e.*, l.titulo, u.nome 
                FROM emprestimos e
                JOIN livros l ON e.livro_id = l.id
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.id = ? AND e.devolvido = 0
            """, (emprestimo_id,))
            
            emprestimo = self.cursor.fetchone()
            
            if not emprestimo:
                print("Erro: Empréstimo não encontrado ou já devolvido.")
                return

            # Calcular a multa se tiver atraso
            hoje = datetime.date.today().isoformat()
            data_devolucao = datetime.date.fromisoformat(emprestimo[4])
            multa = 0.00
            
            if datetime.date.today() > data_devolucao:
                dias_atraso = (datetime.date.today() - data_devolucao).days
                multa = dias_atraso * 2.50
                print(f"Livro devolvido com {dias_atraso} dias de atraso! Multa: R${multa:.2f}")
            else:
                print("Livro devolvido no prazo!")
            
            # Registrar a devolução
            self.cursor.execute("""
                UPDATE emprestimos 
                SET devolvido = 1, multa = ? 
                WHERE id = ?
            """, (multa, emprestimo_id))
            
            # Atualizar o status do livro
            self.cursor.execute("""
                UPDATE livros 
                SET disponivel = 1 
                WHERE id = ?
            """, (emprestimo[1],))
            
            self.connection.commit()
            print(f"Livro '{emprestimo[7]}' devolvido por {emprestimo[8]}.")
        except Error as e:
            print(f"Erro ao processar devolução: {e}")

    def listar_emprestimos_ativos(self):
        """Lista todos os empréstimos ativos"""
        print("\n--- EMPRÉSTIMOS ATIVOS ---")
        try:
            self.cursor.execute("""
                SELECT e.id, l.titulo, u.nome, e.data_emprestimo, e.data_devolucao 
                FROM emprestimos e
                JOIN livros l ON e.livro_id = l.id
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.devolvido = 0
            """)
            emprestimos = self.cursor.fetchall()

            if not emprestimos:
                print("Nenhum empréstimo ativo.")
                return

            for emp in emprestimos:
                print(f"ID: {emp[0]} | Livro: {emp[1]} | Usuário: {emp[2]} | "
                      f"Empréstimo: {emp[3]} | Devolução: {emp[4]}")
        except Error as e:
            print(f"Erro ao listar empréstimos: {e}")
    def login(self):
        print("\n=== SISTEMA DE BIBLIOTECA ===")
        print("\n=== LOGIN ===")
        print("1. Login")
        print("0. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            email = input("E-mail: ").strip()
            senha = input("Senha: ").strip()
            self.cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
            usuario = self.cursor.fetchone()
            if usuario:
                print(f"Bem-vindo, {usuario[1]}!")
                self.menu_principal()
            else:
                print("E-mail ou senha incorretos. Tente novamente.")
                self.login()
        else:
            print("Saindo do Sistema...")
            print("Sistema Fechado!")
            exit()
        pass
    # MENU PRINCIPAL
    def menu_principal(self):
        """Exibe o menu principal e gerencia as opções"""
        while True:
            print("\n=== SISTEMA DE BIBLIOTECA ===")
            print("1. Cadastrar livro")
            print("2. Listar livros")
            print("3. Buscar livro")
            print("4. Cadastrar usuário")
            print("5. Listar usuários")
            print("6. Emprestar livro")
            print("7. Devolver livro")
            print("8. Empréstimos ativos")
            print("9. Resetar banco de dados (limpar tudo)")
            print("0. Sair")

            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                self.cadastrar_livro()
            elif opcao == "2":
                self.listar_livros()
            elif opcao == "3":
                self.buscar_livro()
            elif opcao == "4":
                self.cadastrar_usuario()
            elif opcao == "5":
                self.listar_usuarios()
            elif opcao == "6":
                self.emprestar_livro()
            elif opcao == "7":
                self.devolver_livro()
            elif opcao == "8":
                self.listar_emprestimos_ativos()
            elif opcao == "9":
                confirmacao = input("Tem certeza que deseja limpar TODOS os dados? (s/n):")
                if confirmacao.lower() == "s":
                    print("Limpando dados...")
                    print("Dados limpos!")
                    self.resetar_banco_de_dados()
            elif opcao == "0":
                print("Saindo do sistema...")
                print("Sistema Fechado!")
                break
            else:
                print("Opção inválida!")

# Execução do programa
if __name__ == "__main__":
    biblioteca = Biblioteca()
    biblioteca.login()
