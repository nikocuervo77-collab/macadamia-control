import os
import hashlib
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def init_db():
    print(f"Conectando a la base de datos: {DATABASE_URL.split('@')[-1]}") # Mostrar solo el host por seguridad
    engine = create_engine(DATABASE_URL)
    
    # Leer el archivo schema.sql
    with open('schema.sql', 'r') as f:
        sql_script = f.read()

    # PostgreSQL no entiende AUTOINCREMENT igual que SQLite (USA SERIAL)
    # y algunas sintaxis cambian. Vamos a adaptar el script para que sea compatible.
    sql_script = sql_script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql_script = sql_script.replace("INSERT OR IGNORE", "INSERT") # Postgres usa ON CONFLICT
    
    # Ejecutar el script bloque por bloque
    # Nota: Esto es una simplificación. En un entorno real usaríamos migraciones (Alembic)
    with engine.connect() as conn:
        for command in sql_script.split(';'):
            if command.strip():
                try:
                    conn.execute(text(command))
                except Exception as e:
                    # Si falla por 'already exists' lo ignoramos (comportamiento similar a OR IGNORE)
                    if "already exists" in str(e).lower() or "duplicate key" in str(e).lower():
                        continue
                    else:
                        print(f"Error ejecutando comando: {e}")
        
        # Crear un usuario administrador inicial si no existe
        admin_email = "admin@macadamia.com"
        admin_password = "admin_password"
        password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        try:
            # Obtener el ID del rol ADMIN
            result = conn.execute(text("SELECT id FROM roles WHERE name = 'ADMIN'"))
            role = result.fetchone()
            if role:
                admin_role_id = role[0]
                # Insertar admin
                conn.execute(
                    text("INSERT INTO users (email, password_hash, role_id) VALUES (:email, :hash, :role_id) ON CONFLICT (email) DO NOTHING"),
                    {"email": admin_email, "hash": password_hash, "role_id": admin_role_id}
                )
        except Exception as e:
            print(f"Error creando admin: {e}")
            
        conn.commit()
    
    print("¡Base de datos en la nube inicializada y sincronizada con éxito!")

if __name__ == "__main__":
    init_db()
