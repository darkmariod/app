import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.secret_key = "seven_secret_key_2025"

# DB Config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'barberia_seven.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelos
class Sede(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
    barberos = db.relationship('Barbero', backref='sede', lazy=True)

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    duracion = db.Column(db.Integer)

class Barbero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id'))

# Admin Config
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
        return ' <form method="post">User: <input name="user"><br>Pass: <input type="password" name="pass"><br><button>Entrar</button></form>'

admin = Admin(app, name='Seven Admin', index_view=MyAdminIndexView())
admin.add_view(ModelView(Servicio, db.session))
admin.add_view(ModelView(Barbero, db.session))

# Rutas
@app.route("/")
def index():
    servicios = Servicio.query.all()
    return render_template("servicios.html", servicios=servicios)

@app.route("/barberos", methods=["POST"])
def barberos():
    serv_n = request.form.get("servicio")
    barberos_list = Barbero.query.all()
    return render_template("barbero.html", servicio=serv_n, barberos=barberos_list)

@app.route("/confirmacion", methods=["POST"])
def confirmacion():
    serv_n = request.form.get("servicio")
    barbero_n = request.form.get("barbero")
    serv_info = Servicio.query.filter_by(nombre=serv_n).first()
    return render_template("confirmacion.html", servicio=serv_n, barbero=barbero_n, precio=serv_info.precio)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if Sede.query.count() == 0:
            s = Sede(nombre="Barbería Seven")
            db.session.add(s)
            db.session.commit()
            if Servicio.query.count() == 0:
                servs = [Servicio(nombre="Corte Pro", precio=15.0, duracion=45), 
                         Servicio(nombre="Barba", precio=10.0, duracion=30),
                         Servicio(nombre="Combo", precio=22.0, duracion=60)] # Agrega los otros 6 igual
                db.session.bulk_save_objects(servs)
            if Barbero.query.count() == 0:
                db.session.add_all([Barbero(nombre="Josué", sede_id=s.id), Barbero(nombre="Ariel", sede_id=s.id)])
            db.session.commit()
    app.run(host="0.0.0.0", port=5021, debug=True)