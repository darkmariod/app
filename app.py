import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.secret_key = "seven_secret_key_2024"

# --- DB CONFIG ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barberia_seven.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'lux'
db = SQLAlchemy(app)

# --- MODELOS ---
class Sede(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    foto = db.Column(db.String(200)) # Ejemplo: img/banner.jpg
    barberos = db.relationship('Barbero', backref='sede', lazy=True)

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    duracion = db.Column(db.Integer, default=45)

class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(200))
    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id'), nullable=False)

# --- ADMIN PROTEGIDO ---
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not session.get('logged_in'): return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login', methods=['GET', 'POST'])
    def login_view(self):
        if request.method == 'POST':
            if request.form['user'] == 'admin' and request.form['pass'] == 'seven77':
                session['logged_in'] = True
                return redirect(url_for('.index'))
        return '<h2>Login Admin</h2><form method="post">User: <input name="user"><br>Pass: <input type="password" name="pass"><br><button>Entrar</button></form>'

admin = Admin(app, name='Seven Admin', index_view=MyAdminIndexView())
admin.add_view(ModelView(Sede, db.session))
admin.add_view(ModelView(Servicio, db.session))
admin.add_view(ModelView(Barbero, db.session))

# --- FLUJO DE RUTAS ---

@app.route("/")
def index():
    sede_obj = Sede.query.first()
    servicios = Servicio.query.all()
    return render_template("servicios.html", sede=sede_obj.nombre, servicios=servicios)

@app.route("/barberos", methods=["POST"])
def barberos():
    sede_n = request.form.get("sede")
    serv_n = request.form.get("servicio")
    sede_obj = Sede.query.filter_by(nombre=sede_n).first()
    # Solo saldrán los barberos de tu única sede
    lista_barberos = Barbero.query.filter_by(sede_id=sede_obj.id).all()
    return render_template("barbero.html", sede=sede_n, servicio=serv_n, barberos=lista_barberos)

@app.route("/confirmacion", methods=["POST"])
def confirmacion():
    sede_n = request.form.get("sede")
    serv_n = request.form.get("servicio")
    barbero_n = request.form.get("barbero")
    serv_info = Servicio.query.filter_by(nombre=serv_n).first()
    return render_template("confirmacion.html", sede=sede_n, servicio=serv_n, barbero=barbero_n, precio=serv_info.precio, duracion=serv_info.duracion)

@app.route("/exito", methods=["POST"])
def exito():
    # Recibimos todo para el resumen final
    datos = {
        'servicio': request.form.get("servicio"),
        'barbero': request.form.get("barbero"),
        'fecha': request.form.get("fecha"),
        'hora': request.form.get("hora")
    }
    return render_template("exito.html", **datos)

def init_db():
    with app.app_context():
        db.create_all()
        if Sede.query.count() == 0:
            db.session.add(Sede(nombre="Barbería Seven", foto="img/banner.jpg"))
            db.session.commit()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5021, debug=True)