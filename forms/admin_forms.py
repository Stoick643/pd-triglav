"""Forms for admin functionality"""

from flask_wtf import FlaskForm
from wtforms import SubmitField


class UserApprovalForm(FlaskForm):
    """Form for approving pending users"""

    submit = SubmitField("Odobri")


class UserRejectionForm(FlaskForm):
    """Form for rejecting pending users"""

    submit = SubmitField("Zavrni")
