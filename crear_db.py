import sqlite3

def crear_base_de_dades():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Taula Usuari
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contrasenya TEXT NOT NULL
        )
    ''')

    # Taula PerfilFitness
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PerfilFitness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuari_id INTEGER,
            nom TEXT,
            edat INTEGER,
            pes REAL,
            sexe TEXT,
            FOREIGN KEY (usuari_id) REFERENCES Usuari(id)
        )
    ''')

    # Taula Exercici
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Exercici (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            grup_muscular TEXT,
            descripcio TEXT
        )
    ''')

    # Taula Rutina
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Rutina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuari_id INTEGER,
            nom TEXT NOT NULL,
            tipus TEXT,
            FOREIGN KEY (usuari_id) REFERENCES Usuari(id)
        )
    ''')

    # Taula Rutina_Exercici
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Rutina_Exercici (
            rutina_id INTEGER,
            exercici_id INTEGER,
            series INTEGER,
            repeticions INTEGER,
            PRIMARY KEY (rutina_id, exercici_id),
            FOREIGN KEY (rutina_id) REFERENCES Rutina(id),
            FOREIGN KEY (exercici_id) REFERENCES Exercici(id)
        )
    ''')

    # Taula EntrenamentRealitzat
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EntrenamentRealitzat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuari_id INTEGER,
            rutina_id INTEGER,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuari_id) REFERENCES Usuari(id),
            FOREIGN KEY (rutina_id) REFERENCES Rutina(id)
        )
    ''')

    # CATÀLEG COMPLET D'EXERCICIS
    exercicis = [
        ('Press de Banca', 'Pit', 'Empenta horitzontal amb barra'),
        ('Apertures amb mancuernes', 'Pit', 'Treball aïllat de pectoral'),
        ('Flexions', 'Pit', 'Exercici amb pes corporal'),
        ('Sentadeta', 'Cames', 'Flexió de genolls clàssica'),
        ('Premsa de cames', 'Cames', 'Treball de quàdriceps en màquina'),
        ('Extensió de quàdriceps', 'Cames', 'Aïllament de part davantera'),
        ('Curl femoral', 'Cames', 'Part posterior de la cama'),
        ('Dominades', 'Esquena', 'Tracció vertical amb pes corporal'),
        ('Rem amb barra', 'Esquena', 'Tracció horitzontal per densitat'),
        ('Jalon al pit', 'Esquena', 'Tracció vertical en politja'),
        ('Press Militar', 'Espatlles', 'Empenta vertical per deltoides'),
        ('Elevacions laterals', 'Espatlles', 'Aïllament deltoide lateral'),
        ('Curl de bíceps', 'Braços', 'Flexió de colze amb barra'),
        ('Tríceps en politja', 'Braços', 'Extensió de colze'),
        ('Pes Mort', 'Full Body', 'Exercici de força general'),
        ('Burpees', 'Cardio', 'Exercici explosiu metabòlic'),
        ('Plancha', 'Core', 'Isomètric abdominal'),
        ('Crunches', 'Core', 'Abdominals clàssics'),
        ('Zancades', 'Cames', 'Treball unilateral de cama'),
        ('Rem amb mancuerna', 'Esquena', 'Tracció unilateral')
    ]
    
    cursor.executemany('INSERT INTO Exercici (nom, grup_muscular, descripcio) VALUES (?, ?, ?)', exercicis)

    conn.commit()
    conn.close()
    print("Base de dades i catàleg d'exercicis creats correctament.")

if __name__ == '__main__':
    crear_base_de_dades()