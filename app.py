import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'gymprogress_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTES D'ACCÉS (LOGIN / REGISTRE) ---

@app.route('/')
def index():
    if 'usuari_id' in session: return redirect(url_for('dashboard'))
    mode = request.args.get('mode', 'login')
    return render_template('login.html', mode=mode)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    conn = get_db_connection()
    usuari = conn.execute('SELECT * FROM Usuari WHERE email = ? AND contrasenya = ?', (email, password)).fetchone()
    conn.close()
    if usuari:
        session['usuari_id'] = usuari['id']
        session['usuari_nom'] = usuari['nom']
        return redirect(url_for('dashboard'))
    flash('Email o contrasenya incorrectes', 'error')
    return redirect(url_for('index', mode='login'))

@app.route('/registre', methods=['POST'])
def registre():
    nom = request.form.get('nom')
    email = request.form.get('email')
    password = request.form.get('password')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # El nom es guarda aquí per primer cop i és obligatori (NOT NULL)
        cur.execute('INSERT INTO Usuari (nom, email, contrasenya) VALUES (?, ?, ?)', (nom, email, password))
        uid = cur.lastrowid
        cur.execute('INSERT INTO PerfilFitness (usuari_id) VALUES (?)', (uid,))
        conn.commit()
        session['usuari_id'], session['usuari_nom'] = uid, nom
        return redirect(url_for('dashboard'))
    except sqlite3.IntegrityError:
        flash('Aquest correu ja està registrat', 'error')
        return redirect(url_for('index', mode='registre'))
    finally: conn.close()

# --- RUTES PRINCIPALS ---

@app.route('/dashboard')
def dashboard():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    return render_template('dashboard.html', nom=session['usuari_nom'])

@app.route('/perfil')
def perfil():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    dades = conn.execute('SELECT * FROM PerfilFitness WHERE usuari_id = ?', (session['usuari_id'],)).fetchone()
    conn.close()
    return render_template('perfil.html', dades=dades)

# --- LÒGICA DE GENERACIÓ AUTOMÀTICA (CORREGIDA) ---

@app.route('/generar-rutina', methods=['POST'])
def generar_rutina():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    
    # Recollim dades físiques del formulari de perfil
    try:
        edat = int(request.form.get('edat'))
        pes = float(request.form.get('pes'))
        sexe = request.form.get('sexe')
    except (ValueError, TypeError):
        flash("S'han d'introduir valors vàlids per a edat i pes.", "error")
        return redirect(url_for('perfil'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. ACTUALITZEM NOMÉS PerfilFitness (No toquem la taula Usuari)
        cur.execute('''
            UPDATE PerfilFitness 
            SET edat = ?, pes = ?, sexe = ? 
            WHERE usuari_id = ?
        ''', (edat, pes, sexe, session['usuari_id']))

        # 2. LÒGICA DE SELECCIÓ D'EXERCICIS
        if pes > 90:
            nom_pla = "Pla Crema-Greix"
            noms_ex = ['Burpees', 'Flexions', 'Zancades', 'Plancha']
        elif edat < 25:
            nom_pla = "Pla Potència"
            noms_ex = ['Sentadeta', 'Press de Banca', 'Dominades', 'Press Militar']
        else:
            nom_pla = "Pla Manteniment"
            noms_ex = ['Jalon al pit', 'Premsa de cames', 'Curl de bíceps', 'Plancha']

        # 3. CREEM LA RUTINA
        cur.execute('INSERT INTO Rutina (usuari_id, nom, tipus) VALUES (?, ?, ?)', 
                    (session['usuari_id'], nom_pla, 'automatica'))
        rutina_id = cur.lastrowid

        # 4. INSERIM ELS EXERCICIS BUSCANT-LOS PEL NOM AL CATÀLEG
        for n_ex in noms_ex:
            ex_db = cur.execute('SELECT id FROM Exercici WHERE nom = ?', (n_ex,)).fetchone()
            if ex_db:
                cur.execute('''
                    INSERT INTO Rutina_Exercici (rutina_id, exercici_id, series, repeticions) 
                    VALUES (?, ?, 3, 12)
                ''', (rutina_id, ex_db['id']))

        conn.commit()
        flash(f"Perfil actualitzat i rutina '{nom_pla}' generada!", "success")
    
    except Exception as e:
        conn.rollback()
        flash(f"Error en la generació: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('rutines'))

# --- ALTRES RUTES ---

@app.route('/rutines')
def rutines():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    rutines_db = conn.execute('SELECT * FROM Rutina WHERE usuari_id = ?', (session['usuari_id'],)).fetchall()
    
    llista_completa = []
    for r in rutines_db:
        exs = conn.execute('''
            SELECT E.nom, RE.series, RE.repeticions 
            FROM Rutina_Exercici RE 
            JOIN Exercici E ON RE.exercici_id = E.id 
            WHERE RE.rutina_id = ?''', (r['id'],)).fetchall()
        llista_completa.append({'info': r, 'exercicis': exs})
    
    cataleg = conn.execute('SELECT * FROM Exercici').fetchall()
    conn.close()
    return render_template('rutines.html', rutines=llista_completa, cataleg=cataleg)

@app.route('/exercicis')
def exercicis():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    llista = conn.execute('SELECT * FROM Exercici').fetchall()
    conn.close()
    return render_template('exercicis.html', exercicis=llista)

@app.route('/seguiment')
def seguiment():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    rutines = conn.execute('SELECT * FROM Rutina WHERE usuari_id = ?', (session['usuari_id'],)).fetchall()
    historial = conn.execute('''
        SELECT ER.data, R.nom as rutina_nom 
        FROM EntrenamentRealitzat ER 
        JOIN Rutina R ON ER.rutina_id = R.id 
        WHERE ER.usuari_id = ? 
        ORDER BY ER.data DESC''', (session['usuari_id'],)).fetchall()
    conn.close()
    return render_template('seguiment.html', rutines=rutines, historial=historial)

@app.route('/crear-rutina', methods=['POST'])
def crear_rutina():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    nom_r = request.form.get('nom_rutina')
    ex_ids = request.form.getlist('exercici_id')
    ser_l = request.form.getlist('series')
    rep_l = request.form.getlist('reps')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO Rutina (usuari_id, nom, tipus) VALUES (?, ?, ?)', (session['usuari_id'], nom_r, 'manual'))
        rid = cur.lastrowid
        for i in range(len(ex_ids)):
            if ex_ids[i]:
                cur.execute('INSERT INTO Rutina_Exercici VALUES (?, ?, ?, ?)', (rid, ex_ids[i], ser_l[i], rep_l[i]))
        conn.commit()
    finally: conn.close()
    return redirect(url_for('rutines'))

@app.route('/eliminar-rutina/<int:id>', methods=['POST'])
def eliminar_rutina(id):
    if 'usuari_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('DELETE FROM Rutina_Exercici WHERE rutina_id = ?', (id,))
    conn.execute('DELETE FROM Rutina WHERE id = ? AND usuari_id = ?', (id, session['usuari_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('rutines'))

@app.route('/registrar-entrenament', methods=['POST'])
def registrar_entrenament():
    if 'usuari_id' not in session: return redirect(url_for('index'))
    rid = request.form.get('rutina_id')
    conn = get_db_connection()
    conn.execute('INSERT INTO EntrenamentRealitzat (usuari_id, rutina_id) VALUES (?, ?)', (session['usuari_id'], rid))
    conn.commit()
    conn.close()
    return redirect(url_for('seguiment'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)