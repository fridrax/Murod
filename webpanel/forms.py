# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ReplyForm(FlaskForm):
    reply = TextAreaField('Ответ', validators=[DataRequired()])
    status = SelectField('Статус', choices=[('Новая', 'Новая'), ('В работе', 'В работе'), ('Закрыта', 'Закрыта')])
    submit = SubmitField('Сохранить')
