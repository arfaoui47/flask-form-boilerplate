""" write to a SQLite database with forms, templates
    add new record, delete a record, edit/update a record
    """

from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm
from sqlalchemy import create_engine
from wtforms import (
    SubmitField,
    HiddenField,
    StringField,
    IntegerField,
)
from wtforms.validators import InputRequired, NumberRange
from datetime import date

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config["SECRET_KEY"] = "super secret key"

# Flask-Bootstrap requires this line
Bootstrap(app)

# the name of the database; add path if necessary
db_name = "database.sqlite"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_name

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

# each table in the database needs a class to be created for it
# db.Model is required - don't change it
# identify all columns by name and data type
class Entry(db.Model):
    __tablename__ = "entries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    quantity = db.Column(db.Integer)
    updated = db.Column(db.String)

    def __init__(self, name, quantity, updated):
        self.name = name
        self.quantity = quantity
        self.updated = updated


engine = create_engine(f"sqlite:///{db_name}")
Entry.__table__.create(bind=engine, checkfirst=True)


# +++++++++++++++++++++++
# forms with Flask-WTF

# form for add_record and edit_or_delete
# each field includes validation requirements and messages
class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    name = StringField("Name", [InputRequired()])
    quantity = IntegerField(
        "Quantity",
        [InputRequired(), NumberRange(min=1, max=999, message="Invalid range")],
    )
    # updated - date - handled in the route
    updated = HiddenField()
    submit = SubmitField("Add Record")


def email_data(subject, name, quantity, updated):
    # format body as html table
    body = f"""<html>
            <table width="600" style="border:1px solid #333">
            <tr>
            <td align="center">head</td>
            </tr>
            <tr>
            <td align="center">
                body 
                <table align="center" width="300" border="0" cellspacing="0" cellpadding="0" style="border:1px solid #ccc;">
                <tr>
                    <td> Name  </td>
                    <td> {name} </td>
                </tr>
                <tr>
                    <td> Quantity  </td>
                    <td> {quantity} </td>
                </tr>
                <tr>
                    <td> Updated  </td>
                    <td> {updated} </td>
                </tr>
                </table>
            </td>
            </tr>
            </table>
            </html>"""

    return subject, body


def stringdate():
    today = date.today()
    date_list = str(today).split("-")
    # build string in format 01-01-2000
    date_string = date_list[1] + "-" + date_list[2] + "-" + date_list[0]
    return date_string


# +++++++++++++++++++++++
# routes
@app.route("/", methods=["GET", "POST"])
def index():
    # get a list of unique values in the style column
    form1 = AddRecord()
    if form1.validate_on_submit():
        name = request.form["name"]
        quantity = request.form["quantity"]
        updated = stringdate()
        record = Entry(name, quantity, updated)
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        # create a message to send to the template
        message = f"The data for {name} Entry has been submitted."
        # update email subject
        subject = "New Entry"
        email_subject, body = email_data(subject, name, quantity, updated)
        return render_template(
            "index.html", message=message, subject=email_subject, body=body
        )
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash(
                    "Error in {}: {}".format(getattr(form1, field).label.text, error),
                    "error",
                )
        return render_template("index.html", form1=form1)


# +++++++++++++++++++++++
# error routes
# https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/#registering-an-error-handler


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "error.html",
            pagetitle="404 Error - Page Not Found",
            pageheading="Page not found (Error 404)",
            error=e,
        ),
        404,
    )


@app.errorhandler(405)
def form_not_posted(e):
    return (
        render_template(
            "error.html",
            pagetitle="405 Error - Form Not Submitted",
            pageheading="The form was not submitted (Error 405)",
            error=e,
        ),
        405,
    )


@app.errorhandler(500)
def internal_server_error(e):
    return (
        render_template(
            "error.html",
            pagetitle="500 Error - Internal Server Error",
            pageheading="Internal server error (500)",
            error=e,
        ),
        500,
    )


# +++++++++++++++++++++++

if __name__ == "__main__":
    app.run(debug=True)
