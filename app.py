import ast
import csv
from email import message
import io
import os
from flask import Flask, Response, render_template, url_for, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask_mail import Mail, Message


konekcija = mysql.connector.connect(
 passwd="", # lozinka za bazu
 user="root", # korisničko ime
 database="evidencija_studenata", # ime baze
 port=3306, # port na kojem je mysql server
 auth_plugin='mysql_native_password' # ako se koristi mysql 8.x
)
kursor = konekcija.cursor(dictionary=True)

app = Flask(__name__)
app.secret_key = "tajni_kljuc_aplikacije"
UPLOAD_FOLDER = "static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "evidencija.atvss@gmail.com"
app.config["MAIL_PASSWORD"] = "atvss123loz"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)



def send_email(ime, prezime, email, lozinka):
    msg = Message(subject="Korisnički nalog",sender="ATVSS Evidencija studenata",recipients=[email],)
    msg.html = render_template("email.html", ime=ime, prezime=prezime, lozinka=lozinka)
    mail.send(msg)
    return "Sent"


def ulogovan():
    if "ulogovani_korisnik" in session:
        return True
    else:
        return False

def rola():
    if ulogovan():
        return ast.literal_eval(session["ulogovani_korisnik"]).pop("rola")        

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/export/<tip>")
def export(tip):
    switch = {"studenti": "SELECT * FROM studenti","korisnici": "SELECT * FROM korisnici","predmeti": "SELECT * FROM predmeti",}
    upit = switch.get(tip)
    kursor.execute(upit)
    rezultat = kursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rezultat:red = []
    for value in row.values():red.append(str(value))
    writer.writerow(red)
    output.seek(0)
    return Response(output,mimetype="text/csv",headers={"Content-Disposition": "attachment;filename=" + tip + ".csv"},)

#___________________________________________________________________________________________________________________________________________________________LOGIN I LOGOUT
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template("login.html")
    if request.method=='POST':
        forma = request.form
        if forma["email"] == '' or forma["lozinka"]== '':
            message="Sva polja moraju biti popunjena!"
            return render_template("login.html",message=message)
        else:    
            forma = request.form
            upit = "SELECT * FROM korisnici WHERE email=%s"
            vrednost = (forma["email"],)
            kursor.execute(upit, vrednost)
            korisnik = kursor.fetchone()
            if check_password_hash(korisnik["lozinka"], forma["lozinka"]):# upisivanje korisnika u sesiju
                session["ulogovani_korisnik"] = str(korisnik) 
                return redirect(url_for("studenti"))
            else:
                return render_template("login.html")

@app.route("/logout", methods=['GET'])
def logout():
    session.pop("ulogovani_korisnik", None)
    return redirect(url_for("login"))




#___________________________________________________________________________________________________________________________________________________________KORISNICI


@app.route("/korisnici", methods=['GET'])
def korisnici():
    if ulogovan():
        strana = request.args.get('page', '1')
        offset = int(strana) * 4 - 4
        prethodna_strana = ""
        sledeca_strana = "/studenti?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)
        upit="SELECT * FROM korisnici LIMIT 4 OFFSET %s"
        vrednost=(offset,)
        kursor.execute(upit,vrednost)
        korisnici=kursor.fetchall()
        return render_template("korisnici.html", korisnici=korisnici, strana=strana,sledeca_strana=sledeca_strana,prethodna_strana=prethodna_strana)
    else:
        return redirect(url_for('login'))
        
@app.route("/korisnik_novi", methods=['GET','POST'])
def korisnik_novi():
    if ulogovan():
        if request.method=='GET':
            return render_template("korisnik_novi.html")
        elif request.method=='POST':
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
    else:
        return redirect(url_for('login'))        

@app.route("/korisnik_izmena/<id>", methods=['GET','POST'])
def korisnik_izmena(id):
    if ulogovan():
        if request.method=='GET':
            upit="SELECT * FROM korisnici WHERE id=%s"
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            korisnik=kursor.fetchone()
            return render_template("korisnik_izmena.html", korisnik=korisnik)
        elif request.method=='POST':
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
    else:
        return redirect(url_for('login'))        

@app.route("/korisnik_brisanje/<id>", methods=['POST'])
def korisnik_brisanje(id):
    if ulogovan():
        upit = """DELETE FROM korisnici WHERE id=%s"""
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("korisnici"))
    else:
        return redirect(url_for('login'))

#___________________________________________________________________________________________________________________________________________________________STUDENTI



@app.route("/studenti", methods=['GET'])
def studenti():
    if ulogovan():
        strana = request.args.get('page', '1')
        offset = int(strana) * 4 - 4
        prethodna_strana = ""
        sledeca_strana = "/studenti?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)
            
        args = request.args.to_dict()
        order_by = 'id'
        order_type = 'asc'
            
        if "order_by" in args:
            order_by = args["order_by"].lower()
            if ("prethodni_order_by" in args and args["prethodni_order_by"] == args["order_by"]):
                if args["order_type"] == "asc":
                    order_type = "desc"
        s_ime = "%%"
        s_prezime = "%%"
        s_broj_indeksa = "%%"
        s_god_studija = "%%"
        s_prosek_ocena_od = "0"
        s_prosek_ocena_do = "10"
        if "prosek_ocena_od" in args:
            if args["prosek_ocena_od"]=="":
                s_prosek_ocena_od = "0"
            else:
                s_prosek_ocena_od = args["prosek_ocena_od"]
        if "prosek_ocena_do" in args:
            if args["prosek_ocena_do"]=="":
                s_prosek_ocena_do = "10"
            else:
                    s_prosek_ocena_do = args["prosek_ocena_do"]  
        s_espb_od ="0"
        s_espb_do = "240"  
        if "espb_od" in args:
            if args["espb_od"]=="":
                s_espb_od = "0"
            else:
                s_espb_od = args["espb_od"]
        if "espb_do" in args:
            if args["espb_do"]=="":
                s_espb_do = "240"
            else:
                s_espb_do = args["espb_do"] 
        if "ime" in args:
            s_ime = "%" + args["ime"] + "%"
        if "prezime" in args:
            s_prezime = "%" + args["prezime"] + "%"
        if "broj_indeksa" in args:
            s_broj_indeksa = "%" + args["broj_indeksa"] + "%"
        if "god_studija" in args:
            s_god_studija = "%" + args["god_studija"] + "%"  
            
        upit = "SELECT * FROM studenti WHERE ime LIKE %s AND prezime LIKE %s AND broj_indeksa LIKE %s AND godina_studija LIKE %s AND espb >= %s AND espb <= %s AND prosek_ocena >= %s AND prosek_ocena <= %s ORDER BY " + order_by + " " + order_type + " LIMIT 4 OFFSET %s"

        vrednosti = (
                s_ime,
                s_prezime,
                s_broj_indeksa,
                s_god_studija,
                s_espb_od,
                s_espb_do,
                s_prosek_ocena_od,
                s_prosek_ocena_do,
                offset,
                )
            
        kursor.execute(upit,vrednosti)
        studenti = kursor.fetchall()
        
        return render_template('studenti.html', studenti=studenti, rola=rola(), strana=strana,sledeca_strana=sledeca_strana,prethodna_strana=prethodna_strana,order_type=order_type, args = args)
    else:
        return redirect(url_for('login'))


@app.route("/student/<id>", methods=['GET'])
def student(id):
    if ulogovan():
        upit="SELECT * FROM studenti WHERE id=%s"
        vrednost=(id,)
        kursor.execute(upit, vrednost)
        student=kursor.fetchone()

        upit="""SELECT p.sifra, p.naziv, p.godina_studija, p.obavezni_izborni, p.espb, o.ocena, o.id 
                FROM ocene o INNER JOIN predmeti p 
                ON p.id = o.predmet_id 
                INNER JOIN studenti s ON s.id = o.student_id 
                WHERE o.student_id=%s"""
        vrednost=(id,)
        kursor.execute(upit, vrednost)
        predmeti_ocene=kursor.fetchall()
        upit="""select * from predmeti where predmeti.id not in (SELECT predmet_id from ocene where student_id=%s) """
        vrednost=(id,)
        kursor.execute(upit,vrednost)
        predmeti=kursor.fetchall()
        return render_template("/student.html", student=student,rola=rola(), predmeti_ocene=predmeti_ocene, predmeti=predmeti)
    else:
        return redirect(url_for('login'))

@app.route("/student_novi", methods=['GET','POST'])
def student_novi():
    if rola() == "profesor":
        return redirect(url_for("studenti"))
    if ulogovan():
        if request.method=='GET':
            return render_template("student_novi.html")
        if request.method=='POST':
            forma=request.form
            naziv_slike = ""
            if "slika" in request.files:
                file = request.files["slika"]
                if file.filename:
                    naziv_slike = forma['jmbg'] + file.filename
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], naziv_slike))
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
                naziv_slike,
            )

            upit=""" INSERT INTO
                    studenti(ime,ime_roditelja,prezime,broj_indeksa,godina_studija,jmbg,datum_rodjenja,broj_telefona,email,slika)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            kursor.execute(upit, vrednosti)
            konekcija.commit()#sacuvati izmene u bazi
            return redirect(url_for("studenti"))
    else:
        return redirect(url_for('login'))        

@app.route("/student_izmena/<id>", methods=['GET','POST'])
def student_izmena(id):
    if ulogovan():
        if request.method=='GET':
            upit="SELECT * FROM studenti WHERE id=%s"
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            student=kursor.fetchone()
            return render_template("student_izmena.html", student=student)
        if request.method=='POST':
            forma=request.form
            naziv_slike = ""
            if "slika" in request.files:
                file = request.files["slika"]
                if file.filename:
                    naziv_slike = forma['jmbg'] + file.filename
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], naziv_slike))
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
                naziv_slike,
                id,
            )
            upit=""" UPDATE studenti  SET
                    ime=%s,ime_roditelja=%s,prezime=%s,broj_indeksa=%s,godina_studija=%s,jmbg=%s,datum_rodjenja=%s,broj_telefona=%s,email=%s,slika=%s WHERE id=%s
            """
            kursor.execute(upit, vrednosti)
            konekcija.commit()#sacuvati izmene u bazi
            return redirect(url_for("studenti"))
    else:
        return redirect(url_for('login'))         

@app.route("/student_brisanje/<id>", methods=['POST','GET'])
def student_brisanje(id):
    if ulogovan():
        upit = """DELETE FROM studenti WHERE id=%s"""
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("studenti"))
    else:
        return redirect(url_for('login'))
##___________________________________________________________________________________________________________________________________________________________PREDMETI



@app.route("/predmeti", methods=['GET'])
def predmeti():
    if ulogovan():
        strana = request.args.get('page', '1')
        offset = int(strana) * 4 - 4
        prethodna_strana = ""
        sledeca_strana = "/studenti?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)
        upit="SELECT * FROM predmeti LIMIT 4 OFFSET %s"
        vrednost=(offset,)
        kursor.execute(upit,vrednost)
        predmeti=kursor.fetchall()
        return render_template("predmeti.html", predmeti=predmeti,strana=strana,sledeca_strana=sledeca_strana,prethodna_strana=prethodna_strana)
    else:
        return redirect(url_for('login'))

@app.route("/predmet_novi", methods=['GET','POST'])
def predmet_novi():
    if ulogovan():
        if request.method=='GET':
            return render_template("predmet_novi.html")
        if request.method=='POST':
            forma=request.form
            vrednosti=(
                forma['sifra'],
                forma['naziv'],
                forma['godina_studija'],
                forma['espb'],
                forma['obavezni_izborni'],
            )
            upit=""" INSERT INTO
                    predmeti(sifra,naziv,godina_studija,espb,obavezni_izborni)
                    VALUES (%s,%s,%s,%s,%s)
            """
            kursor.execute(upit, vrednosti)
            konekcija.commit()#sacuvati izmene u bazi
            return redirect(url_for("predmeti"))
    else:
        return redirect(url_for('login'))        

@app.route("/predmet_izmena/<id>", methods=['GET','POST'])
def predmet_izmena(id):
    if ulogovan():
        if request.method=='GET':
            upit="SELECT * FROM predmeti WHERE id=%s"
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            predmet=kursor.fetchone()
            return render_template("predmet_izmena.html", predmet=predmet)
        if request.method=='POST':
            forma=request.form
            vrednosti=(
                forma['sifra'],
                forma['naziv'],
                forma['godina_studija'],
                forma['espb'],
                forma['obavezni_izborni'],
                id,
            )
            upit="""  UPDATE predmeti SET
                    sifra=%s,naziv=%s,godina_studija=%s,espb=%s,obavezni_izborni=%s WHERE id=%s
            """
            kursor.execute(upit, vrednosti)
            konekcija.commit()#sacuvati izmene u bazi
            return redirect(url_for("predmeti"))
    else:
        return redirect(url_for('login'))        

@app.route("/predmet_brisanje/<id>", methods=['POST'])
def predmet_brisanje(id):
    if ulogovan():
        upit = """DELETE FROM predmeti WHERE id=%s"""
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("predmeti"))
    else:
        return redirect(url_for('login'))      

#___________________________________________________________________________________________________________________________________________________________OCENE



@app.route("/ocena_nova/<id>", methods=['POST'])
def ocena_nova(id):
    if ulogovan():
        # Dodavanje ocene u tabelu ocene
        forma = request.form
        predmet_id=forma['odabran_predmet']
        print(predmet_id)


        upit = """INSERT INTO ocene(student_id, predmet_id, ocena, datum) VALUES(%s, %s, %s, %s)"""
        vrednosti = (id, predmet_id, forma['ocena'], forma['datum'],)
        kursor.execute(upit, vrednosti)
        konekcija.commit()

        # Računanje proseka ocena
        upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id=%s"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        prosek_ocena = kursor.fetchone()

        # Računanje ukupno espb
        upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_id FROM ocene WHERE student_id=%s)"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        espb = kursor.fetchone()

        # Izmena tabele student
        upit = "UPDATE studenti SET espb=%s, prosek_ocena=%s WHERE id=%s"
        vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], id)
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for('student', id=id))
    else:
        return redirect(url_for('login')) 

@app.route("/ocena_brisanje/<id>", methods=['POST'])
def ocena_brisanje(id):
    if ulogovan():
        upit="""SELECT student_id FROM ocene WHERE id=%s"""
        vrednost=(id,)
        kursor.execute(upit, vrednost)
        student=kursor.fetchone()
        st_id=student['student_id']


        upit = """DELETE FROM ocene WHERE id=%s"""
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()

        # Računanje proseka ocena
        upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id=%s"
        vrednost = (st_id,)
        kursor.execute(upit, vrednost)
        prosek_ocena = kursor.fetchone()

        # Računanje ukupno espb
        upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_id FROM ocene WHERE student_id=%s)"
        vrednost = (st_id,)
        kursor.execute(upit, vrednost)
        espb = kursor.fetchone()

        # Izmena tabele student
        upit = "UPDATE studenti SET espb=%s, prosek_ocena=%s WHERE id=%s"
        vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], st_id)
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for('student', id=st_id))
    else:
        return redirect(url_for('login'))

@app.route("/ocena_izmena/<id>", methods=['GET','POST'])
def ocena_izmena(id):
    if ulogovan():
        if request.method=='GET':
            upit="SELECT * FROM ocene WHERE id=%s"
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            ocene=kursor.fetchone()
            print(id)

            upit="SELECT * FROM ocene INNER JOIN predmeti ON ocene.predmet_id=predmeti.id WHERE ocene.id=%s"
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            predmet=kursor.fetchone()
            print(predmet)
            return render_template("ocena_izmena.html", ocene=ocene, predmet=predmet)

        if request.method=='POST':
            forma = request.form
            print(forma)
            upit = """UPDATE ocene SET  ocena=%s, datum=%s WHERE id=%s"""
            vrednost = (forma['ocena'],forma['datum'],id)
            kursor.execute(upit, vrednost)
            konekcija.commit()

            upit="""SELECT student_id FROM ocene WHERE id=%s"""
            vrednost=(id,)
            kursor.execute(upit, vrednost)
            student=kursor.fetchone()
            st_id=student['student_id']
            # Računanje proseka ocena
            
            upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id=%s"
            vrednost = (st_id,)
            kursor.execute(upit, vrednost)
            prosek_ocena = kursor.fetchone()

        # Računanje ukupno espb
            upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_id FROM ocene WHERE student_id=%s)"
            vrednost = (st_id,)
            kursor.execute(upit, vrednost)
            espb = kursor.fetchone()

        # Izmena tabele student
            upit = "UPDATE studenti SET espb=%s, prosek_ocena=%s WHERE id=%s"
            vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], st_id)
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('student', id=st_id))
    else:
        return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)