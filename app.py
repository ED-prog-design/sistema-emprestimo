import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_para_sessoes"
# Forçando o Render a atualizar o sistema

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

    # Cria tabela de materiais incluindo o campo 'usuario_atual'
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
        # NOVO: Dicionário estático com chaves fixas (1 letra e 4 números) pré-geradas.
        # Dessa forma, a senha NUNCA mais muda quando o Render reiniciar.
        usuarios_fixos = {
            "930": "R7142",
            "940": "K9053",
            "950": "M4180",
            "960": "X2931",
            "970": "A8542",
            "980": "P1094",
            "990": "J6325",
            "1000": "F7410",
            "1010": "V3628",
            "1020": "D9514",
            "931": "H4821",
            "941": "L7036",
            "951": "N1592",
            "961": "Q8473",
            "971": "W2615",
            "981": "G3940",
            "991": "Y5281",
            "1001": "B6749",
            "1011": "C1358",
            "1021": "Z8204",
        }

        materiais_base = ["Furadeira", "Martelete", "Enxada", "Pá", "Carriola"]

        for user_id, chave in usuarios_fixos.items():
            cursor.execute(
                "INSERT INTO usuarios (id, chave_acesso) VALUES (?, ?)",
                (user_id, chave),
            )

            # Status inicial 'INDisponível' e 'usuario_atual' começa sendo o próprio dono
            for mat in materiais_base:
                cursor.execute(
                    """
                    INSERT INTO materiais (nome, numerador, usuario_atual, status) 
                    VALUES (?, ?, ?, ?)
                """,
                    (mat, user_id, user_id, "INDisponível"),
                )

        conn.commit()
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
        if material["numerador"] == usuario_logado:
            if novo_status == "Ocupada":
                usuario_destino = novo_usuario_atual
            else:
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
            flash(f"Material '{material['nome']}' atualizado com sucesso!")
        else:
            flash("Erro: Permissão negada.")

    conn.close()
    return redirect(url_for("painel"))


@app.route("/logout")
def logout():
    session.pop("usuario_logado", None)
    return redirect(url_for("logout"))


if __name__ == "__main__":
    inicializar_banco()
    app.run(host="0.0.0.0", port=5000)