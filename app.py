import random
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_para_sessoes"

DATABASE = "sistema.db"


def obter_conexao():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()

    # Cria tabela de usuários
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            chave_acesso TEXT
        )
    """
    )

    # NOVO: Cria tabela de materiais incluindo o campo 'usuario_atual'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            numerador TEXT,
            usuario_atual TEXT,
            status TEXT,
            FOREIGN KEY (numerador) REFERENCES usuarios (id),
            FOREIGN KEY (usuario_atual) REFERENCES usuarios (id)
        )
    """
    )

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        lista_usuarios = [
            "930",
            "940",
            "950",
            "960",
            "970",
            "980",
            "990",
            "1000",
            "1010",
            "1020",
            "931",
            "941",
            "951",
            "961",
            "971",
            "981",
            "991",
            "1001",
            "1011",
            "1021",
        ]
        materiais_base = ["Furadeira", "Martelete", "Enxada", "Pá", "Carriola"]

        print("\n=== ATENÇÃO: NOVAS CHAVES DE ACESSO GERADAS ===")
        for user_id in lista_usuarios:
            letra = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            numeros = "".join(random.choices("0123456789", k=4))
            chave = f"{letra}{numeros}"

            cursor.execute(
                "INSERT INTO usuarios (id, chave_acesso) VALUES (?, ?)",
                (user_id, cancellation_token := chave),
            )
            print(f"Usuário: {user_id} | Chave: {chave}")

            # MUDANÇA: Status inicial agora é 'INDisponível' e 'usuario_atual' começa sendo o próprio dono
            for mat in materiais_base:
                cursor.execute(
                    """
                    INSERT INTO materiais (nome, numerador, usuario_atual, status) 
                    VALUES (?, ?, ?, ?)
                """,
                    (mat, user_id, user_id, "INDisponível"),
                )

        conn.commit()
        print("=========================================\n")
    conn.close()


@app.route("/", methods=["GET", "POST"])
def login():
    if "usuario_logado" in session:
        return redirect(url_for("painel"))

    if request.method == "POST":
        usuario_input = request.form["usuario"].strip()
        chave_input = request.form["chave"].strip()

        conn = obter_conexao()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE id = ? AND chave_acesso = ?",
            (usuario_input, chave_input),
        ).fetchone()
        conn.close()

        if user:
            session["usuario_logado"] = user["id"]
            return redirect(url_for("painel"))
        else:
            flash("Usuário ou Chave de Acesso incorretos!")

    return render_template("index.html", tela="login")


@app.route("/painel")
def painel():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    conn = obter_conexao()
    todos_materiais = conn.execute("SELECT * FROM materiais").fetchall()
    # Busca a lista completa de IDs de usuários para preencher o campo de empréstimo (select)
    usuarios = conn.execute("SELECT id FROM usuarios ORDER BY id").fetchall()
    lista_ids = [u["id"] for u in usuarios]
    conn.close()

    return render_template(
        "index.html",
        tela="painel",
        materiais=todos_materiais,
        lista_usuarios=lista_ids,
        usuario_atual_logado=session["usuario_logado"],
    )


@app.route("/alterar_status/<int:material_id>", methods=["POST"])
def alterar_status(material_id):
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    usuario_logado = session["usuario_logado"]
    novo_status = request.form["novo_status"]
    novo_usuario_atual = request.form.get("novo_usuario_atual")

    conn = obter_conexao()
    material = conn.execute(
        "SELECT * FROM materiais WHERE id = ?", (material_id,)
    ).fetchone()

    if material:
        # REGRA DE SEGURANÇA: Apenas o dono original (numerador) altera
        if material["numerador"] == usuario_logado:

            # Lógica de negócio solicitada:
            if novo_status == "Ocupada":
                # Se mudou para Ocupado, usa o ID selecionado no formulário
                usuario_destino = novo_usuario_atual
            else:
                # Se for Disponível ou INDisponível, volta a ficar vinculado ao dono original
                usuario_destino = material["numerador"]

            conn.execute(
                """
                UPDATE materiais 
                SET status = ?, usuario_atual = ? 
                WHERE id = ?
            """,
                (novo_status, usuario_destino, material_id),
            )
            conn.commit()
            flash(
                f"Material '{material['nome']}' atualizado com sucesso!"
            )
        else:
            flash("Erro: Permissão negada.")

    conn.close()
    return redirect(url_for("painel"))


@app.route("/logout")
def logout():
    session.pop("usuario_logado", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)