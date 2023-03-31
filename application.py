#General Flask Imports
from flask import Flask, render_template, request, session

#For MySQL Database connection
import mysql.connector as mysql

#For OTP validation though mail
from flask_mail import Mail, Message
from random import randint

#For Art Generation
import io
import os
import warnings
from PIL import Image
import PIL
import base64
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

#Importing external files

#Intialization
app = Flask(__name__)
app.secret_key = "richard"



#Connection to the mail server to send OTP
mail = Mail(app)
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'richarda0538@gmail.com'
app.config['MAIL_PASSWORD'] = 'zydmmtbspdsoknat'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


#Connection to the Database
db = mysql.connect(
    host='localhost',
    user='root',
    password='Richard@538',
    database='imagipicto'
)
cur = db.cursor()



#Index Page
@app.route('/')
def index():
    return render_template("index.html")

#Index Page-2 (After Login/Register)
@app.route('/index2')
def index2():
    return render_template("index2.html")

#Home Page
@app.route('/home')
def homePage():
    return render_template("home_page.html")



#MODULE1 - Registration, Login, Forgot Password, Logout

#Calling Login_Register File
@app.route('/loginRegister')
def loginRegister():
    return render_template('login_register.html')

#Validating Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    le = request.form['emailid']
    lp = request.form['loginpassword']

    session['emailid'] = le
    session['loginpassword'] = lp
    sql = "SELECT email, password FROM user_data WHERE email=%s"
    email = [(session['emailid'])]
    cur.execute(sql, email)
    user = cur.fetchone()
    if user:
        if session['emailid'] == user[0] and session['loginpassword'] == user[1]:
            return render_template('index2.html')
        else:
            return render_template('login_register.html', abc='Invalid Login!')
    else:
        return render_template('login_register.html', abc='No Rocords Found! Please Register!!')

#Validating Register
@app.route('/register', methods=['POST'])
def register():
    fn = request.form['firstname']
    ln = request.form['lastname']
    re = request.form['emailid']
    rp = request.form['registerpassword']
    cp = request.form['confirmpassword']
    rflag = 0
    session['emailid'] = re
    sql = "SELECT email FROM user_data WHERE email=%s"
    ue = [(session['emailid'])]
    cur.execute(sql, ue)
    regdata = cur.fetchone()
    if regdata:
        if session['emailid'] == regdata[0]:
            rflag = 1
            return render_template('login_register.html', abc="Account already Exists!", rflag=rflag, email=re, firstname=fn, lastname=ln)
    else:
        if fn.isalpha() and ln.isalpha():
            if rp == cp:
                sql = "INSERT INTO user_data(firstname, lastname, email, password) VALUES(%s, %s, %s, %s)"
                val = (fn, ln, re, rp)
                cur.execute(sql, val)
                db.commit()
                return render_template('login_register.html', abc='Registered Successfully! Please Login', rflag=0)
            else:
                rflag = 1
                return render_template('login_register.html', abc='Passwords did not match!', rflag=rflag, email=email, firstname=fn, lastname=ln)
        else:
            rflag = 1
            return render_template('login_register.html', abc='First and Last Names should be characters', rflag=rflag, email=email)

#Calling Forgot Password Page
@app.route('/forgot')
def forgotPassword():
    return render_template('forgot_password.html')

#Generate OTP and send to the mail
@app.route('/getOtp', methods=['POST'])
def getOtp():
    email = request.form['emailid']
    sql = "SELECT email FROM user_data WHERE email=%s"
    cur.execute(sql, [email])
    user = cur.fetchone()
    if user:
        if email == user[0]:
            msg = Message(subject='OTP', sender='richardson00538@gmail.com', recipients=[email])
            session['otp'] = randint(000000, 999999)
            msg.body = str(session['otp'])
            mail.send(msg)
            return render_template('forgot_password.html', res='OTP sent!', email=str(email)[2:-2])
        else:
            return render_template('login_register.html', abc='No Rocords Found! Please Register!!')
    else:
        return render_template('login_register.html', abc='No Rocords Found! Please Register!!')
    

#Validating the OTP obtained
@app.route('/validate', methods=["POST"])
def validate():
    user_otp = request.form['otp']
    if session['otp'] == int(user_otp):
        return render_template('reset_password.html')
    return render_template('forgot_password.html', abc="Incorrect OTP!")

#Resetting the Password
@app.route('/reset', methods=['POST'])
def reset():
    newpass = request.form['newpass']
    confirmpass = request.form['confirmpass']
    if newpass==confirmpass:
        sql = "UPDATE user_data SET password=%s WHERE email=%s"
        val = [newpass, (session['emailid'])]
        cur.execute(sql, val)
        db.commit()
        return render_template('login_register.html', abc="Password Upadted! Please Re-Login")
    else:
        return render_template('reset_password.html', abc="Invaid!")


#MODULE2 - Art Generation, Meme Generation, Criminal Face GEneration, Poster PResentation

#Connection to the server
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
os.environ['STABILITY_KEY'] = 'sk-OUPUAgV1ZDxAPn93Bt88kCuz79sAeiUQra2I7yMkVTRUR2Lx'
stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'],
    verbose=True,
    engine="stable-diffusion-v1-5"
)

#Function to generate art image
def generateimage(text):
    for resp in text:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                insertImage(session['emailid'], artifact.binary)
                img = Image.open(io.BytesIO(artifact.binary))
                data = io.BytesIO()
                img.save(data, "JPEG")
                encoded_img_data = base64.b64encode(data.getvalue())
                #img.show()
    return encoded_img_data.decode('utf-8')

#ART GENERATION

#Calling Art Generation Page(art)
@app.route('/art')
def art():
    return render_template('art_generation.html')

#Generating the art image based on given input
@app.route('/generateArt', methods=["POST"])
def generateArt():
    text = request.form['t1']
    prompt="detailed 4k resolution image of " + text
    answers = stability_api.generate(
    prompt=prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("art_generation.html", img_data=img_data, prompt=text)


#Criminal Face Generation

#Calling Criminal Face Generation Page
@app.route('/criminal_face_generation')
def criminal_face():
    return render_template('criminal_face_generation.html')

#Generating face based on the given text
@app.route('/generateFace', methods=["POST"])
def generateFace():
    gender = request.form['gender']
    age = request.form['age']
    hair = request.form['hair']
    face = request.form['face']
    eyes = request.form['eyes']
    nose = request.form['nose']
    lips = request.form['lips']
    skin = request.form['skin']
    t2 = request.form['t2']
    prompt = "a neat realistic, 8k clear coloured front centered image, "+gender+" of "+age+" years old, "+hair+" hair, "+face+" face, "+eyes+" eyes, "+nose+" nose, "+lips+" lips, "+skin+" skin, "+t2
    answers = stability_api.generate(
    prompt=prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("criminal_face_generation.html", img_data=img_data, gender=gender, age=age, hair=hair, face=face, eyes=eyes, nose=nose, lips=lips, skin=skin, t2=t2)

#Meme Generation

#Calling Criminal Face Generation Page
@app.route('/memes_generation')
def memes():
    return render_template('memes_generation.html')

#Generating the art image based on given input
@app.route('/generateMeme', methods=["POST"])
def generateMeme():
    prompt=request.form['meme']
    answers = stability_api.generate(
    prompt="a meme on "+prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("memes_generation.html", img_data=img_data, prompt=prompt)

#Poster Generation

#Calling Poster Generation Page
@app.route('/poster_generation')
def poster():
    return render_template('poster_generation.html')

#Generating the poster based on given input
@app.route('/generatePoster', methods=["POST"])
def generatePoster():
    prompt=request.form['poster']
    answers = stability_api.generate(
    prompt="a poster on "+prompt,
    #seed=992446758,
    steps=30,
    cfg_scale=8.0,
    width=512,
    height=512,
    samples=1,
    sampler=generation.SAMPLER_K_DPMPP_2M
    )
    img_data = generateimage(answers)
    return render_template("poster_generation.html", img_data=img_data, prompt=prompt)


#MODULE3 - Profile Page

#Connection to the user searched Database
imageDB = mysql.connect(
        host='localhost',
        database='imagipicto',
        user='root',
        password='Richard@538'
)
cursor = imageDB.cursor()

#Storing Searched Images into Database
def insertImage(email, photo):
    print("Inserting Image into Database")
    sql_insert_image_query = """ INSERT INTO userimages(email, photo) VALUES (%s,%s)"""
    insert_image_tuple = (email, photo)
    result = cursor.execute(sql_insert_image_query, insert_image_tuple)
    imageDB.commit()
    print("Image inserted successfully into table")

#Extracting Images from the Database
def extractImage(email):
    print("Reading BLOB data from python_employee table")
    sql_fetch_image_query = """SELECT * from userimages where email = %s"""
    cursor.execute(sql_fetch_image_query, (email,))
    record = cursor.fetchall()
    pic = []
    for i in record:
        pic.append(i[1])
    return pic

def openImg(pic):
    if not pic:
        return None
    img = Image.open(io.BytesIO(pic))
    data = io.BytesIO()
    img.save(data, "JPEG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data.decode('utf-8')

#Calling Profile Page
@app.route('/profile')
def profilePage():
    sql = "SELECT firstname, lastname FROM user_data WHERE email=%s"
    email = [(session['emailid'])]
    cur.execute(sql, email)
    user = cur.fetchone()
    images = extractImage(session['emailid'])
    for i in range(len(images), 15):
        images.append(None)
    return render_template('profile_page.html', name=str(user[0]+" "+user[1]), email=str(email)[2:-2], img1=openImg(images[0]), img2=openImg(images[1]),img3=openImg(images[2]), img4=openImg(images[3]),img5=openImg(images[4]), img6=openImg(images[5]), img7=openImg(images[6]),img8=openImg(images[7]), img9=openImg(images[8]), img10=openImg(images[9]), img11=openImg(images[10]), img12=openImg(images[11]), img13=openImg(images[12]), img14=openImg(images[13]), img15=openImg(images[14]))

@app.route('/display')
def display():
    return None

#Running the code
if __name__ == "__main__":
    app.run(debug=True)