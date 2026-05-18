import os
import secrets
from PIL import Image
from flask import Flask, flash, url_for, render_template, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp
from datetime import date
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')

    def __repr__(self):
        return f"{self.name}, {self.surname}, {self.dob}, {self.class_name}, {self.phone}, {self.image_file}"


@app.route("/")
@app.route("/home")
def home():
    students = Student.query.all()
    return render_template('index.html', students=students)


@app.route("/about")
def about():
    return render_template('about.html', title="About")


@app.route("/add-student", methods=['GET', 'POST'])
def add():
    form = New_StudentForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.picture.data)
        student = Student(name=form.name.data,
                          surname=form.surname.data,
                          dob=form.dob.data,
                          class_name=form.class_name.data,
                          phone=form.phone.data,
                          image_file=picture_file
                          )
        db.session.add(student)
        db.session.commit()
        flash(f'Student: {form.name.data}, has been successfully added', "success")

        return redirect(url_for('student_detail', id=student.id))
    return render_template("add_student.html", title="New Student", form=form)


@app.route("/search")
def search():
    query = request.args.get("query", "").lower()
    results = Student.query.filter(
              Student.name.ilike(f"%{query}%")).all()

    return jsonify([{
        "id": s.id,
        "name": s.name,
        "surname": s.surname
    } for s in results])


@app.route("/view_all")
def view_all():
    students = Student.query.all()
    student_count = Student.query.count()
    return render_template("view_all.html", students=students,
                           title="View_all", student_count=student_count)


@app.route("/student/<int:id>")
def student_detail(id):
    student = db.get_or_404(Student, id)
    return render_template("student_detail.html", student=student)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/student_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/student/<int:id>/update", methods=["GET", "POST"])
def update_student(id):
    student = db.get_or_404(Student, id)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            student.image_file = picture_file
        student.name = form.name.data
        student.surname = form.surname.data
        student.dob = form.dob.data
        student.class_name = form.class_name.data
        student.phone = form.phone.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(f"/student/{id}")
    elif request.method == 'GET':
        form.name.data = student.name
        form.surname.data = student.surname
        form.dob.data = student.dob
        form.class_name.data = student.class_name
        form.phone.data = student.phone

    image_file = url_for('static', filename='student_pics/' + student.image_file)
    return render_template("update_student.html",
                           student=student, form=form, title='Update',
                           image_file=image_file)


@app.route("/student/<int:id>/delete", methods=["POST"])
def delete_student(id):
    student = db.get_or_404(Student, id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for('view_all'))

class New_StudentForm(FlaskForm):
    name = StringField('First Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    surname = StringField('Surname',
                          validators=[DataRequired(), Length(min=2, max=20)])
    dob = DateField("Date Of Birth",
                    validators=[DataRequired()])
    class_name = StringField('Class Name',
                             validators=[DataRequired(), Length(max=3)])
    phone = StringField('Phone Number',
                        validators=[
                            DataRequired(),
                            Length(min=10, max=15),
                            Regexp(r'^\+?[0-9]+$', message="Enter a valid phone number")
                        ])
    picture = FileField(
        'Update Student Picture',
        validators=[
            FileRequired(message="Please upload a student picture."),
            FileAllowed(['png', 'jpg', 'jpeg'], "Only .png, .jpg, .jpeg files are allowed.")
        ]
    )
    submit = SubmitField('ADD')

    def validate_dob(self, dob):
        if dob.data > date.today():
            raise ValidationError("Date of Birth cannot be in the future.")
        if dob.data.year < 1900:
            raise ValidationError("Please enter a realistic date of birth.")


class UpdateAccountForm(FlaskForm):
    name = StringField('First Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    surname = StringField('Surname',
                          validators=[DataRequired(), Length(min=2, max=20)])
    dob = DateField("Date Of Birth",
                    validators=[DataRequired()])
    class_name = StringField('Class Name',
                             validators=[DataRequired(), Length(max=3)])
    phone = StringField('Phone Number',
                        validators=[
                            DataRequired(),
                            Length(min=10, max=15),
                            Regexp(r'^\+?[0-9]+$', message="Enter a valid phone number")
                        ])
    picture = FileField('Update Student Picture', validators=[FileAllowed(['png', 'jpg', 'jpeg'])])

    submit = SubmitField('Save Changes')

    def validate_dob(self, dob):
        if dob.data > date.today():
            raise ValidationError("Date of Birth cannot be in the future.")
        if dob.data.year < 1900:
            raise ValidationError("Please enter a realistic date of birth.")


if __name__ == "__main__":
    app.run(debug=True)