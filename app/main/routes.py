from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required

from app import db
from app.main.forms import EditProfileForm, EmptyForm, EquationForm, MessageForm
from app.main import bp
from app.models import User, Equation, Message, Notification


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = EquationForm()
    if form.validate_on_submit():
        equation = Equation(x_var=form.x_var.data, y_var=form.y_var.data, operator=form.operator.data,
                            author=current_user)
        equation.calculate()
        db.session.add(equation)
        db.session.commit()
        flash('Equation has been submitted!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    equations = current_user.followed_equations().paginate(page, current_app.config['EQUATIONS_PER_PAGE'], False)
    next_url = url_for('main.index', page=equations.next_num) if equations.has_next else None
    prev_url = url_for('main.index', page=equations.prev_num) if equations.has_prev else None
    return render_template('index.html', title='Home', form=form, equations=equations.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    equations = user.equations.order_by(Equation.timestamp.desc()).paginate(
        page, current_app.config['EQUATIONS_PER_PAGE'], False)
    next_url = url_for('main.user', page=equations.next_num) if equations.has_next else None
    prev_url = url_for('main.user', page=equations.prev_num) if equations.has_prev else None
    form = EmptyForm()
    return render_template('user.html', title='Home', user=user, equations=equations.items, next_url=next_url,
                           prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Error, you cannot follow yourself.')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {username}!')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Error, you cannot unfollow yourself.')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are no longer following user: {username}!')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    equations = Equation.query.order_by(Equation.timestamp.desc()).paginate(page,
                                                                            current_app.config['EQUATIONS_PER_PAGE'],
                                                                            False)
    next_url = url_for('main.explore', page=equations.next_num) if equations.has_next else None
    prev_url = url_for('main.explore', page=equations.prev_num) if equations.has_prev else None
    return render_template('index.html', title='Explore', equations=equations.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(f'Your message has been sent.')
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
