import datetime
import re

from flask import Flask
from flask import render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Userstore(db.Model):
    __tablename__ = 'userstore'
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(20))
    password = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, default=datetime.datetime.now)


class Location(db.Model):
    loc_id = db.Column(db.Integer, primary_key= True)
    loc_name = db.Column(db.String(20),unique = True, nullable = False)

    def __repr__(self):
        return f"Location('{self.loc_id}','{self.loc_name}')"
        #return "Location('{self.loc_id}','{self.loc_name}')"


class Product(db.Model):
    prod_id = db.Column(db.Integer, primary_key= True)
    prod_name = db.Column(db.String(20),unique = True ,nullable = False)
    prod_qty = db.Column(db.Integer, nullable = False)
    def __repr__(self):
        return f"Product('{self.prod_id}','{self.prod_name}','{self.prod_qty}')"


class Movement(db.Model):
    mid = db.Column(db.Integer, primary_key= True)
    ts = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    frm = db.Column(db.String(20), nullable = False)
    to = db.Column(db.String(20), nullable = False)
    pname = db.Column(db.String(20), nullable = False)
    pqty = db.Column(db.Integer, nullable = False)

    def __repr__(self):
        return f"Movement('{self.mid}','{self.ts}','{self.frm}','{self.to}','{self.pname}','{self.pqty}')"


class Balance(db.Model):
    bid = db.Column(db.Integer, primary_key= True,nullable = False)
    product = db.Column(db.String(20), nullable = False)
    location = db.Column(db.String(20),nullable = False)
    quantity = db.Column(db.Integer, nullable = False)

    def __repr__(self):
        return f"Balance('{self.bid}','{self.product}','{self.location}','{self.quantity}')"
    

class addproduct(FlaskForm):
    prodname = StringField('Product Name', validators=[DataRequired()])
    prodqty = IntegerField('Quantity', validators=[NumberRange(min=5, max=1000000),DataRequired()])
    prodsubmit = SubmitField('Save Changes')


class editproduct(FlaskForm):
    editname = StringField('Product Name', validators=[DataRequired()])
    editqty = IntegerField('Quantity', validators=[NumberRange(min=5, max=1000000),DataRequired()])
    editsubmit = SubmitField('Save Changes')


class addlocation(FlaskForm):
    locname = StringField('Location Name', validators=[DataRequired()])
    locsubmit = SubmitField('Save Changes')


class editlocation(FlaskForm):
    editlocname = StringField('Location Name', validators=[DataRequired()])
    editlocsubmit = SubmitField('Save Changes')


class moveproduct(FlaskForm):
    mprodname = SelectField('Product Name')
    src = SelectField('Source')
    destination = SelectField('Destination')
    mprodqty = IntegerField('Quantity', validators=[NumberRange(min=5, max=1000000),DataRequired()])
    movesubmit = SubmitField('Move')

with app.app_context(): 
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:                # Checking for session login
        return redirect( url_for('overview') )

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        usr = Userstore.query.filter_by(uname = username).first()
        if usr == None:
            flash('User Not Found', category='error')
            return redirect( url_for('login') )

        elif username == usr.uname and password == usr.password:
            session['username'] = username  # saving session for login
            return redirect( url_for('overview') )

        else:
            flash('Wrong Credentials. Check Username and Password Again', category="error")

    return render_template("login.html")


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        uname = request.form['uname']
        password = request.form['pass']
        cnfrm_password = request.form['cpass']

        query = Userstore.query.filter_by(uname = uname).first()

        if query != None:
            if uname == str(query.uname):
                flash('Username already taken')
                return redirect( url_for('registration') )
        
        if password != cnfrm_password:
            flash('Passwords do not match')
            return redirect( url_for('registration') )

        regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
        pattern = re.compile(regex)

        match = re.search(pattern, password)
        
        if match:
            user = Userstore(uname = uname, password = password)
            db.session.add(user)
            db.session.commit()
            flash('Staff Registred Successfully', category='info')
            return redirect( url_for('login') )
        else:
            flash('Password should contain one Uppercase, one special character, one numeric character')
            return redirect( url_for('registration') )
    return render_template('staff_registration.html')


@app.route("/Overview")
def overview():
    balance = Balance.query.all()
    exists = bool(Balance.query.all())
    if exists== False :
        flash(f'Add products,locations and make transfers to view','info')
    return render_template('overview.html' ,balance=balance)


@app.route("/Product", methods = ['GET','POST'])
def product():
    form = addproduct()
    eform = editproduct()
    details = Product.query.all()
    exists = bool(Product.query.all())
    if exists== False and request.method == 'GET' :
            flash(f'Add products to view','info')
    elif eform.validate_on_submit() and request.method == 'POST':

        p_id = request.form.get("productid","")
        pname = request.form.get("productname","")
        details = Product.query.all()
        prod = Product.query.filter_by(prod_id = p_id).first()
        prod.prod_name = eform.editname.data
        prod.prod_qty= eform.editqty.data
        Balance.query.filter_by(product=pname).update(dict(product=eform.editname.data))
        Movement.query.filter_by(pname=pname).update(dict(pname=eform.editname.data))
        try:
            db.session.commit()
            flash(f'Your product  has been updated!', 'success')
            return redirect('/Product')
        except IntegrityError :
            db.session.rollback()
            flash(f'This product already exists','danger')
            return redirect('/Product')
        return render_template('product.html',title = 'Products',details=details,eform=eform)

    elif form.validate_on_submit() :
        product = Product(prod_name=form.prodname.data,prod_qty=form.prodqty.data)
        db.session.add(product)
        try:
            db.session.commit()
            flash(f'Your product {form.prodname.data} has been added!', 'success')
            return redirect(url_for('product'))
        except IntegrityError :
            db.session.rollback()
            flash(f'This product already exists','danger')
            return redirect('/Product')
    return render_template('product.html',title = 'Products',eform=eform,form = form,details=details)


@app.route("/Location", methods = ['GET', 'POST'])
def loc():
    form = addlocation()
    lform = editlocation()
    details = Location.query.all()
    exists = bool(Location.query.all())
    if exists== False and request.method == 'GET':
            flash(f'Add locations  to view','info')
    if lform.validate_on_submit() and request.method == 'POST':
        p_id = request.form.get("locid","")
        locname = request.form.get("locname","")
        details = Location.query.all()
        loc = Location.query.filter_by(loc_id = p_id).first()
        loc.loc_name = lform.editlocname.data
        Balance.query.filter_by(location=locname).update(dict(location=lform.editlocname.data))
        Movement.query.filter_by(frm=locname).update(dict(frm=lform.editlocname.data))
        Movement.query.filter_by(to=locname).update(dict(to=lform.editlocname.data))
        try:
            db.session.commit()
            flash(f'Your location  has been updated!', 'success')
            return redirect(url_for('loc'))
        except IntegrityError :
            db.session.rollback()
            flash(f'This location already exists','danger')
            return redirect('/Location')
    elif form.validate_on_submit() :
        loc = Location(loc_name=form.locname.data)
        db.session.add(loc)
        try:
            db.session.commit()
            flash(f'Your location {form.locname.data} has been added!', 'success')
            return redirect(url_for('loc'))
        except IntegrityError :
            db.session.rollback()
            flash(f'This location already exists','danger')
            return redirect('/Location')
    return render_template('loc.html',title = 'Locations',lform=lform,form = form,details=details)


@app.route("/Transfers", methods = ['GET', 'POST'])
def move():
    form = moveproduct()

    details = Movement.query.all()
    pdetails = Product.query.all()
    exists = bool(Movement.query.all())
    if exists== False and request.method == 'GET' :
            flash(f'Transfer products  to view','info')
    #----------------------------------------------------------
    prod_choices = Product.query.with_entities(Product.prod_name,Product.prod_name).all()
    loc_choices = Location.query.with_entities(Location.loc_name,Location.loc_name).all()
    prod_list_names = [('Product_Name','Product_Name')]
    src_list_names,dest_list_names=[('Warehouse','Warehouse')],[('Warehouse','Warehouse')]
    prod_list_names+=prod_choices
    src_list_names+=loc_choices
    dest_list_names+=loc_choices
    #passing list_names to the form for select field
    form.mprodname.choices = prod_list_names
    form.src.choices = src_list_names
    form.destination.choices = dest_list_names
    #--------------------------------------------------------------
    #send to db
    if form.validate_on_submit() and request.method == 'POST' :

        timestamp = datetime.datetime.now()
        boolbeans = check(form.src.data,form.destination.data,form.mprodname.data,form.mprodqty.data)
        if boolbeans == False:
            flash(f'Retry with lower quantity than source location', 'danger')
        elif boolbeans == 'same':
            flash(f'Source and destination cannot be the same.', 'danger')
        elif boolbeans == 'no prod':
            flash(f'Not enough products in this loaction .Please add products', 'danger')
        else:
            mov = Movement(ts=timestamp,frm=form.src.data,to = form.destination.data,
                           pname=form.mprodname.data,pqty=form.mprodqty.data)
            db.session.add(mov)
            db.session.commit()
            flash(f'Your  activity has been added!', 'success')
        return redirect(url_for('move'))
    return render_template('move.html',title = 'Transfers',form = form,details= details)

def check(frm,to,name,qty):
    if frm == to:
        a = 'same'
        return a
    elif frm == 'Warehouse' and to != 'Warehouse':
        prodq = Product.query.filter_by(prod_name=name).first()
        print(prodq)
        if prodq.prod_qty >= qty:
            prodq.prod_qty -= qty
            bal = Balance.query.filter_by(location=to, product=name).first()
            a = str(bal)
            if (a == 'None'):
                new = Balance(product=name, location=to, quantity=qty)
                db.session.add(new)
            else:
                bal.quantity += qty
            db.session.commit()
        else:
            return False
    elif to == 'Warehouse' and frm != 'Warehouse':
        bal = Balance.query.filter_by(location=frm, product=name).first()
        a = str(bal)
        if (a == 'None'):
            return 'no prod'
        else:
            if bal.quantity >= qty:
                prodq = Product.query.filter_by(prod_name=name).first()
                prodq.prod_qty = prodq.prod_qty + qty
                bal.quantity -= qty
                db.session.commit()
            else:
                return False

    else:  # from='?' and to='?'
        bl = Balance.query.filter_by(location=frm, product=name).first()  # check if from location is in Balance
        a = str(bl)
        if (a == 'None'):  # if not
            return 'no prod'

        elif (bl.quantity - 100) > qty:
            # if from qty is sufficiently large, check to  in Balance
            bal = Balance.query.filter_by(location=to, product=name).first()
            a = str(bal)
            if a == 'None':
                # if not add entry
                new = Balance(product=name, location=to, quantity=qty)
                db.session.add(new)
                bl = Balance.query.filter_by(location=frm, product=name).first()
                bl.quantity -= qty
                db.session.commit()
            else:  # else add to 'from' qty and minus from 'to' qty
                bal.quantity += qty  # if yes,add to to qty
                bl = Balance.query.filter_by(location=frm, product=name).first()
                bl.quantity -= qty
                db.session.commit()
        else:
            return False
@app.route("/delete")
def delete():
    type = request.args.get('type')
    if type == 'product':
        pid = request.args.get('p_id')
        product = Product.query.filter_by(prod_id=pid).delete()
        db.session.commit()
        flash(f'Your product  has been deleted!', 'success')
        return redirect(url_for('product'))
        return render_template('product.html',title = 'Products')
    else:
        pid = request.args.get('p_id')
        loc = Location.query.filter_by(loc_id = pid).delete()
        db.session.commit()
        flash(f'Your location  has been deleted!', 'success')
        return redirect(url_for('loc'))
        return render_template('loc.html',title = 'Locations')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('logged out successfully .')
    return redirect( url_for('login') )



if __name__=="__main__":
    app.run(debug=True)
    app.secret_key = "super secret key"
