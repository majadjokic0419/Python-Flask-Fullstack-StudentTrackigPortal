from flask import Flask, render_template, url_for, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector


konekcija = mysql.connector.connect(
 passwd="", # lozinka za bazu
 user="root", # korisničko ime
 database="evidencija_studenata", # ime baze
 port=3306, # port na kojem je mysql server
 auth_plugin='mysql_native_password' # ako se koristi mysql 8.x
)
kursor = konekcija.cursor(dictionary=True)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")



#__________________________________________________________LOGIN I LOGOUT
@app.route("/login", methods=['GET'])
def login():
    return render_template("login.html")

@app.route("/logout", methods=['GET'])
def logout():
    return render_template("notyet.html")




#___________________________________________________________KORISNICI
@app.route("/korisnik_izmena", methods=['GET','POST'])
def korisnik_izmena1():
    return render_template("korisnik_izmena.html") 

@app.route("/korisnici", methods=['GET'])
def korisnici():
    upit="SELECT * FROM korisnici"
    kursor.execute(upit)
    korisnici=kursor.fetchall()
    return render_template("korisnici.html", korisnici=korisnici)

@app.route("/korisnik_novi", methods=['GET','POST'])
def korisnik_novi():
    if request.method=='GET':
        return render_template("korisnik_novi.html")
    if request.method=='POST':
        forma=request.form
        hesovana_lozinka=generate_password_hash(forma['lozinka'])
        vrednosti=(
            forma['ime'],
            forma['prezime'],
            forma['email'],
            forma['rola'],
            hesovana_lozinka
        )
        upit=""" INSERT INTO
                korisnici(ime,prezime,email,rola,lozinka)
                VALUES (%s,%s,%s,%s,%s)
        """
        kursor.execute(upit, vrednosti)
        konekcija.commit()#sacuvati izmene u bazi
        return redirect(url_for("korisnici"))

@app.route("/korisnik_izmena/<id>", methods=['GET','POST'])
def korisnik_izmena(id):
    if request.method=='GET':
        upit="SELECT * FROM korisnici WHERE id=%s"
        vrednost=(id,)
        kursor.execute(upit, vrednost)
        korisnik=kursor.fetchone()
        return render_template("korisnik_izmena.html", korisnik=korisnik)
    if request.method=='POST':
        upit = """UPDATE korisnici SET ime=%s,prezime=%s,email=%s,rola=%s,lozinka=%sWHERE id=%s"""
        forma = request.form
        vrednosti = (
            forma["ime"],
            forma["prezime"],
            forma["email"],
            forma["rola"],
            forma["lozinka"],
            id,
            )
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("korisnici"))

@app.route("/korisnik_brisanje/<id>", methods=['POST'])
def korisnik_brisanje(id):
    upit = """DELETE FROM korisnici WHERE id=%s"""
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("korisnici"))


#___________________________________________________________STUDENTI



@app.route("/studenti", methods=['GET'])
def studenti():
    upit="SELECT * FROM studenti"
    kursor.execute(upit)
    studenti=kursor.fetchall()
    print(studenti)
    return render_template("studenti.html", studenti=studenti)

@app.route("/student/<id>", methods=['GET'])
def student(id):
    upit="SELECT * FROM studenti WHERE id=%s"
    vrednost=(id,)
    kursor.execute(upit, vrednost)
    student=kursor.fetchone()
    return render_template("/student.html", student=student)

@app.route("/student_novi", methods=['GET','POST'])
def student_novi():
    if request.method=='GET':
        return render_template("student_novi.html")
    if request.method=='POST':
        forma=request.form
        vrednosti=(
            forma['ime'],
            forma['ime_roditelja'],
            forma['prezime'],
            forma['broj_indeksa'],
            forma['godina_studija'],
            forma['jmbg'],
            forma['datum_rodjenja'],
            forma['broj_telefona'],
            forma['email'],
        )
        upit=""" INSERT INTO
                studenti(ime,ime_roditelja,prezime,broj_indeksa,godina_studija,jmbg,datum_rodjenja,broj_telefona,email)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        kursor.execute(upit, vrednosti)
        konekcija.commit()#sacuvati izmene u bazi
        return redirect(url_for("studenti"))

@app.route("/student_izmena/<id>", methods=['GET','POST'])
def student_izmena(id):
    if request.method=='GET':
        return render_template("student_novi.html")
    if request.method=='POST':
        forma=request.form
        vrednosti=(
            forma['ime'],
            forma['ime_roditelja'],
            forma['prezime'],
            forma['broj_indeksa'],
            forma['godina_studija'],
            forma['jmbg'],
            forma['datum_rodjenja'],
            forma['broj_telefona'],
            forma['email'],
            id,
        )
        upit=""" UPDATE studenti  SET
                ime=%s,ime_roditelja=%s,prezime=%s,broj_indeksa=%s,godina_studija=%s,jmbg=%s,datum_rodjenja=%s,broj_telefona=%s,email=%s WHERE id=%s
        """
        kursor.execute(upit, vrednosti)
        konekcija.commit()#sacuvati izmene u bazi
        return redirect(url_for("studenti"))

@app.route("/student_brisanje/<id>", methods=['GET'])
def student_brisanje(id):
    upit = """DELETE FROM studenti WHERE id=%s"""
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("studenti"))

#___________________________________________________________PREDMETI



@app.route("/predmeti", methods=['GET'])
def predmeti():
    upit="SELECT * FROM predmeti"
    kursor.execute(upit)
    studenti=kursor.fetchall()
    return render_template("predmeti.html", predmeti=predmeti)
   

@app.route("/predmet_novi", methods=['GET'])
def predmet_novi():
    return render_template("predmet_novi.html")

@app.route("/predmet_izmena/<id>", methods=['GET'])
def predmet_izmena(id):
    id1=id
    return render_template("predmet_novi.html")

@app.route("/predmet_brisanje/<id>", methods=['GET'])
def predmet_brisanje(id):
    id1=id
    return render_template("notyet.html") 

#___________________________________________________________OCENE



@app.route("/ocena_nova/<id>", methods=['POST'])
def ocena_nova(id):
    # Dodavanje ocene u tabelu ocene
    upit = """INSERT INTO ocene(student_id, predmet_id, ocena, datum)VALUES(%s, %s, %s, %s)"""
    forma = request.form
    vrednosti = (id, forma['predmet_id'], forma['ocena'], forma['datum'])
    kursor.execute(upit, vrednosti)
    konekcija.commit()

    # Računanje proseka ocena
    upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id=%s"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    prosek_ocena = kursor.fetchone()

    # Računanje ukupno espb
    upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_idFROM ocene WHERE student_id=%s)"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    espb = kursor.fetchone()

    # Izmena tabele student
    upit = "UPDATE studenti SET espb=%s, prosek_ocena=%s WHERE id=%s"
    vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], id)
    kursor.execute(upit, vrednosti)
    konekcija.commit()
    return redirect(url_for('student', id=id))

@app.route("/ocena_brisanje/<id>", methods=['POST'])
def ocena_brisanje(id):
    upit = """DELETE FROM ocene WHERE id=%s"""
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    
    # Računanje proseka ocena
    upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id=%s"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    prosek_ocena = kursor.fetchone()

    # Računanje ukupno espb
    upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_idFROM ocene WHERE student_id=%s)"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    espb = kursor.fetchone()

    # Izmena tabele student
    upit = "UPDATE studenti SET espb=%s, prosek_ocena=%s WHERE id=%s"
    vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], id)
    kursor.execute(upit, vrednosti)
    konekcija.commit()
    return redirect(url_for('student', id=id))

@app.route("/ocena_izmena/<id>", methods=['GET'])
def ocena_izmena(id):
    upit = """UPDATE ocene SET student_id=%s, predmet_id=%s, ocena=%s, datum=%s WHERE id=%s"""
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()



if __name__ == "__main__":
    app.run(debug=True)