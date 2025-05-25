# app.py
from flask import Flask, render_template, redirect, url_for, session, request, flash
from forms import LoginForm, ReplyForm
from models import get_all_tickets, get_ticket_by_id, update_ticket_status, add_ticket_reply
from utils import login_required
from config import SECRET_KEY, ADMIN_LOGIN, ADMIN_PASSWORD
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

@app.template_filter('datetime_format')
def datetime_format(value, format="%d.%m.%Y %H:%M"):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime(format)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime(format)
    except Exception:
        return str(value)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == ADMIN_LOGIN and form.password.data == ADMIN_PASSWORD:
            session['user_logged'] = True
            return redirect(url_for('tickets'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_logged', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def tickets():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    tickets = get_all_tickets(search, status)
    return render_template('tickets.html', tickets=tickets, search=search, status=status)

@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('tickets'))
    form = ReplyForm()
    if form.validate_on_submit():
        add_ticket_reply(ticket_id, form.reply.data)
        update_ticket_status(ticket_id, form.status.data)
        flash('Ответ и статус обновлены', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket_id))
    return render_template('ticket_detail.html', ticket=ticket, form=form)

if __name__ == '__main__':
    app.run(debug=True)
