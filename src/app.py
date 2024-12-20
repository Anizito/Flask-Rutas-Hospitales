from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from config import config
from a_star import load_coordinates, read_adj_list, astar, generar_grafo_completo, generar_camino_encontrado
import networkx as nx
import matplotlib
matplotlib.use('Agg')

# Models:
from models.ModelUser import ModelUser

# Entities:
from models.entities.User import User

app = Flask(__name__)

csrf = CSRFProtect()
db = MySQL(app)
login_manager_app = LoginManager(app)


@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Invalid password...")
                return render_template('auth/login.html')
        else:
            flash("User not found...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    try:
        cursor = db.connection.cursor()
        cursor.execute(
            """
            SELECT hospital_origen, hospital_destino, distancia, fecha
            FROM historial
            WHERE user_id = %s
            ORDER BY fecha DESC
            """,
            (current_user.id,)
        )
        historial = cursor.fetchall() 
        print("Historial cargado correctamente.")
    except Exception as e:
        print(f"Error al cargar el historial: {e}")
        historial = []

    return render_template('home.html', historial=historial)

@app.route('/hospitales', methods=['GET'])
def hospitales():
    ruta_csv = os.path.join(os.path.dirname(__file__), 'hospitales.csv')
    datos = pd.read_csv(ruta_csv, sep=';')
    return render_template('hospitals.html', datos=datos.to_dict('records'))


@app.route('/buscar', methods=['POST'])
def buscar():
    hospital1 = request.form['hospital1']
    hospital2 = request.form['hospital2']
    
    print(f"Hospital origen: {hospital1}, Hospital destino: {hospital2}")
    
    adj_list_file = os.path.join(os.path.dirname(__file__), 'lista_adyacencia.txt')
    coords_file = os.path.join(os.path.dirname(__file__), 'hospitales.csv')

    try:
        adj_list = read_adj_list(adj_list_file)
        print("Lista de adyacencia cargada correctamente.")
        coords = load_coordinates(coords_file)
        print("Coordenadas cargadas correctamente.")
    except Exception as e:
        print(f"Error al cargar archivos: {e}")
        return "Error al cargar los datos", 500

    G = nx.Graph()

    try:
        for node, neighbors in adj_list.items():
            lat, lon = coords.get(node, (0, 0))  
            G.add_node(node, lat=lat, lon=lon)
            for neighbor, weight in neighbors:
                G.add_edge(node, neighbor, weight=weight)
        print("Grafo creado correctamente.")
    except Exception as e:
        print(f"Error al crear el grafo: {e}")
        return "Error al crear el grafo", 500

    try:
        cost, path = astar(G, hospital1, hospital2)
        print(f"Camino encontrado: {path} con costo {cost}")
    except Exception as e:
        print(f"Error al ejecutar A*: {e}")
        flash("Ingrese identificadores válidos")
        return redirect(url_for('home'))
   
    try:
        generar_camino_encontrado(G, path)
    except Exception as e:
        print(f"Error al generar los gráficos: {e}")
        return "Error al generar gráficos", 500

    ruta_csv = os.path.join(os.path.dirname(__file__), 'hospitales.csv')
    datos = pd.read_csv(ruta_csv, sep=';')

    hospital1_nombre = datos.loc[datos['id_eess'] == int(hospital1), 'nombre'].values[0]
    hospital2_nombre = datos.loc[datos['id_eess'] == int(hospital2), 'nombre'].values[0]

    path_info = []
    for hop in path:
        hospital_info = datos.loc[datos['id_eess'] == int(hop)]
        path_info.append({
            'id': hop,
            'nombre': hospital_info['nombre'].values[0],
            'lat': hospital_info['latitud'].values[0],
            'lng': hospital_info['longitud'].values[0]
        })

    try:
        cursor = db.connection.cursor()
        cursor.execute(
            """
            INSERT INTO historial (user_id, hospital_origen, hospital_destino, distancia)
            VALUES (%s, %s, %s, %s)
            """,
            (current_user.id, hospital1_nombre, hospital2_nombre, cost)
        )
        db.connection.commit()
        print("Búsqueda guardada en el historial.")
    except Exception as e:
        print(f"Error al guardar en el historial: {e}")
    return render_template(
        'resultado_busqueda.html',
        hospital1=hospital1_nombre,
        hospital2=hospital2_nombre,
        cost=cost,
        path=path_info,
        grafo_completo='grafo_completo.png',
        camino_encontrado='camino_encontrado.png'
    )

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run() 