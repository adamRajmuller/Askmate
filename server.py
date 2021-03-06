from flask import Flask, request, render_template, redirect, session, flash
import util
import data_manager

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def index():
    user_id = data_manager.get_userid_by_username(session.get('username'))
    questions = data_manager.get_five_latest_submitted_titles_with_ids_from_table('question')
    header = data_manager.get_column_names_of_table(data_manager.question_db)[4]
    return render_template('index_head.html', questions=questions, header=header, user_id=user_id)


@app.route('/list')
@app.route('/list/')
def route_list():
    user_id = data_manager.get_userid_by_username(session.get('username'))
    questions = data_manager.import_from_db(data_manager.question_db)
    headers = data_manager.get_column_names_of_table(data_manager.question_db)
    if request.args:
        questions = data_manager.sort_table(data_manager.question_db, request.args['order_by'],
                                            request.args['order_direction'])
    return render_template('list_head.html', questions=questions, headers=headers, user_id=user_id)


@app.route('/user-list')
@app.route('/user-list/')
def route_user_list():
    user_id = data_manager.get_userid_by_username(session.get('username'))
    users = data_manager.import_from_db(data_manager.users_db)
    headers = data_manager.get_column_names_of_table(data_manager.users_db)
    if request.args:
        users = data_manager.sort_table(data_manager.users_db, request.args['order_by'],
                                            request.args['order_direction'])
    return render_template('user_list_head.html', users=users, headers=headers, user_id=user_id)


@app.route('/question/<int:question_id>/new-comment', methods=['GET', 'POST'])
@app.route('/answer/<int:answer_id>/new-comment', methods=['GET', 'POST'])
def add_comment(question_id=None, answer_id=None, comment=None, comment_id=-1):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.method == 'GET':
        if request.path.startswith("/q"):
            question_title = data_manager.get_line_data_by_id(data_manager.question_db, question_id)[0]['title']
            return render_template('add_edit_comment_head.html', question_title=question_title, comment=comment,
                                   comment_id=comment_id, user_id=user_id)
        else:
            answer_message = data_manager.get_line_data_by_id(data_manager.answer_db, answer_id)[0]['message']
            return render_template('add_edit_comment_head.html', answer_id=answer_id, answer_message=answer_message,
                                   comment=comment, comment_id=comment_id, user_id=user_id)

    elif request.method == 'POST':
        user_id = data_manager.get_userid_by_username(session.get('username'))
        if request.path.startswith("/q"):
            data_manager.add_comment_to_table(data_manager.comment_db, 'question_id', question_id,
                                              request.form['comment'], util.get_time(), 0, user_id)
        else:
            question_id = data_manager.get_foreign_key_by_id(data_manager.answer_db, 'question_id', answer_id)[0][
                'question_id']
            data_manager.add_comment_to_table(data_manager.comment_db, 'answer_id', answer_id, request.form['comment'],
                                              util.get_time(), 0, user_id)
        return redirect('/question/{}'.format(question_id))


@app.route('/comments/<int:comment_id>/delete')
def delete_comment(comment_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    answer_id = data_manager.get_foreign_key_by_id(data_manager.comment_db, 'answer_id', comment_id)[0]['answer_id']
    if answer_id:
        question_id = data_manager.get_foreign_key_by_id(data_manager.answer_db, 'question_id', answer_id)[0][
            'question_id']
    else:
        question_id = data_manager.get_foreign_key_by_id(data_manager.comment_db, 'question_id', comment_id)[0][
            'question_id']
    if user_id == data_manager.get_foreign_key_by_id(data_manager.comment_db, 'users_id', comment_id)[0]['users_id']:
        data_manager.delete_line_by_id(data_manager.comment_db, comment_id)
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))

@app.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
def edit_comment(comment_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.method == 'GET' and user_id == data_manager.get_foreign_key_by_id(data_manager.comment_db, 'users_id', comment_id)[0]['users_id']:
        comment = data_manager.get_line_data_by_id(data_manager.comment_db, comment_id)
        return render_template('add_edit_comment_head.html', comment_id=comment_id, comment=comment, user_id=user_id)

    elif request.method == 'POST' and user_id == data_manager.get_foreign_key_by_id(data_manager.comment_db, 'users_id', comment_id)[0]['users_id']:
        data_manager.update_comment_message_submt_editedc_by_id(comment_id, request.form['comment'], util.get_time())
    answer_id = data_manager.get_foreign_key_by_id(data_manager.comment_db, 'answer_id', comment_id)[0]['answer_id']
    if answer_id:
        question_id = data_manager.get_foreign_key_by_id(data_manager.answer_db, 'question_id', answer_id)[0][
            'question_id']
    else:
        question_id = data_manager.get_foreign_key_by_id(data_manager.comment_db, 'question_id', comment_id)[0][
            'question_id']
    if not user_id == data_manager.get_foreign_key_by_id(data_manager.comment_db, 'users_id', comment_id)[0]['users_id']:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/user/<int:user_id>')
def route_user(user_id):
    user_reputation = data_manager.get_reputation_by_id(user_id)
    questions_of_user = data_manager.get_lines_data_by_foreign_id(data_manager.question_db, 'users_id', user_id)
    user_answers_questions = data_manager.get_answers_with_their_questions_by_foreign_id('users_id', user_id)
    question_comments = data_manager.get_question_comments_message_with_question_by_foreign_id('users_id', user_id)
    answer_comments = data_manager.get_answer_comments_message_with_answer_and_question_by_foreign_id('users_id', user_id)
    headers_q = data_manager.get_column_names_of_table(data_manager.question_db)
    headers_c = data_manager.get_column_names_of_table(data_manager.comment_db)
    headers_a = data_manager.get_column_names_of_table(data_manager.answer_db)
    return render_template('user_page_head.html', questions_of_user=questions_of_user, user_answers_questions=user_answers_questions,
                           question_comments=question_comments, answer_comments=answer_comments,
                           headers_q=headers_q, headers_a=headers_a, headers_c=headers_c, reputation=user_reputation, user_id=user_id)


@app.route('/question/<int:question_id>')
def route_question(question_id):
    user_id = data_manager.get_userid_by_username(session.get('username'))
    question = data_manager.get_line_data_by_id(data_manager.question_db, question_id)
    headers_q = data_manager.get_column_names_of_table(data_manager.question_db)
    headers_c = data_manager.get_column_names_of_table(data_manager.comment_db)[3:5]
    headers_a = data_manager.get_column_names_of_table(data_manager.answer_db)
    comments_q = data_manager.get_comments_data_by_foreign_id('question_id', question_id)
    answers = data_manager.get_lines_data_by_foreign_id(data_manager.answer_db, 'question_id', question_id)
    filename_q = '/static/image_for_question' + str(question_id) + '.png'
    image_q = util.check_file(filename_q.lstrip("/"))
    tags = data_manager.get_tags(question_id)
    answer_ids = {}
    for answer in answers:
        answer_ids[answer['id']] = [util.check_file('static/image_for_answer' + str(answer['id']) + '.png'),
                                    '/static/image_for_answer' + str(answer['id']) + '.png',
                                    data_manager.get_lines_data_by_foreign_id(data_manager.comment_db, 'answer_id', answer['id'])]
    if user_id:
        answer_statuses = list(map(lambda x: x['accepted_status'],
                                   data_manager.get_lines_data_by_foreign_id(data_manager.answer_db, 'question_id',
                                                                             question_id)))
        voted_questions_of_user = list(map(lambda x: x['question_id'], data_manager.get_foreign_key_by_id(data_manager.user_vote_db,
                                                                                  'question_id', user_id)))
        voted_answers_of_user = list(map(lambda x: x['answer_id'], data_manager.get_foreign_key_by_id(data_manager.user_vote_db, 'answer_id',
                                                                                user_id)))
        return render_template('question_head.html', question_id=question_id, question=question, headers_q=headers_q,
                                   comments_q=comments_q, headers_c=headers_c, answers=answers,
                                   headers_a=headers_a, image_q=image_q, filename_q=filename_q, answer_ids=answer_ids,
                                   tags=tags, user_id=user_id, voted_questions_of_user=voted_questions_of_user,
                                   voted_answers_of_user=voted_answers_of_user, answer_statuses=answer_statuses)
    else:
        return render_template('question_head.html', question_id=question_id, question=question, headers_q=headers_q,
                           comments_q=comments_q, headers_c=headers_c, answers=answers,
                           headers_a=headers_a, image_q=image_q, filename_q=filename_q, answer_ids=answer_ids,
                           tags=tags)


@app.route('/question/<int:question_id>/view_counter')
def route_question_view_counter(question_id):
    data_manager.update_view_number_in_question_by_id(question_id)
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/add-image', methods=['GET', 'POST'])
def add_image(question_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.method == 'GET' and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        return render_template('add-image_head.html', question_id=question_id, user_id=user_id)
    elif request.method == 'POST'and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        url = request.form['URL']
        filename = 'static/image_for_question' + str(question_id) + '.png'
        util.save_image_to_file(url, filename)
        data_manager.update_image_data_by_id(data_manager.question_db, question_id, filename)
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/<int:answer_id>/add-image', methods=['GET', 'POST'])
def add_image_a(question_id, answer_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.method == 'GET' and user_id == data_manager.get_foreign_key_by_id(data_manager.answer_db, 'users_id', answer_id)[0]['users_id']:
        return render_template('add-image_head.html', user_id=user_id)
    elif request.method == 'POST' and user_id == data_manager.get_foreign_key_by_id(data_manager.answer_db, 'users_id', answer_id)[0]['users_id']:
        url = request.form['URL']
        filename = 'static/image_for_answer' + str(answer_id) + '.png'
        util.save_image_to_file(url, filename)
        data_manager.update_image_data_by_id(data_manager.answer_db, answer_id, filename)
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/delete-image')
def delete_question_image(question_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        filename = 'static/image_for_question' + str(question_id) + '.png'
        util.delete_file(filename)
        data_manager.update_image_data_by_id(data_manager.question_db, question_id, 'no image')
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/<int:answer_id>/delete-image')
def delete_answer_image(question_id, answer_id):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if user_id == data_manager.get_foreign_key_by_id(data_manager.answer_db, 'users_id', answer_id)[0]['users_id']:
        filename = 'static/image_for_answer' + str(answer_id) + '.png'
        util.delete_file(filename)
        data_manager.update_image_data_by_id(data_manager.answer_db, answer_id, 'no image')
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/<int:answer_id>', methods=['GET', 'POST'])
@app.route('/question/<int:question_id>/new-answer', methods=['GET', 'POST'])
def post_answer(question_id, answer_id=""):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.path == '/question/' + str(question_id) + '/' + str(answer_id) and request.method == 'GET':
        single_question = data_manager.get_line_data_by_id(data_manager.question_db, question_id)
        question_title = single_question[0]['title']
        answer = data_manager.get_line_data_by_id(data_manager.answer_db, answer_id)[0]
        return render_template('post-answer_head.html', question_title=question_title, answer=answer, answer_id=answer_id, user_id=user_id)

    elif request.path == '/question/' + str(question_id) + '/' + str(answer_id) and request.method == 'POST':
        form_answer = request.form['answer_message']
        data_manager.update_answer(answer_id, form_answer)
        return redirect('/question/{}'.format(question_id))
    else:
        if request.method == 'POST':
            user_id = data_manager.get_userid_by_username(session.get('username'))
            form_answer = request.form['answer_message']
            data_manager.add_answer(question_id, form_answer, user_id)
            return redirect('/question/{}'.format(question_id))
        else:
            single_question = data_manager.get_line_data_by_id(data_manager.question_db, question_id)
            question_title = single_question[0]['title']
            return render_template('post-answer_head.html', question_title=question_title, answer_id=answer_id, user_id=user_id)


@app.route('/add-question', methods=['GET', 'POST'])
@app.route('/add-question/<int:question_id>', methods=['GET', 'POST'])
def add_edit_question(question_id=None):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if question_id and request.method == 'GET' and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:  # edit question
        question = data_manager.get_line_data_by_id(data_manager.question_db, question_id)[0]  # edit get
        return render_template('add_questions_head.html', question=question, question_id=question_id, user_id=user_id)

    elif request.method == 'POST' and question_id and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        title = request.form['question_title']  # edit post
        message = request.form['question_message']
        data_manager.update_question(question_id, title, message)
        return redirect('/question/{}'.format(question_id))

    elif request.method == 'GET' and question_id is None:  # add get
        return render_template('add_questions_head.html', question_id=question_id, user_id=user_id)

    elif request.method == 'POST' and question_id is None:  # add post
        user_id = data_manager.get_userid_by_username(session.get('username'))
        data_manager.add_question(request.form['question_title'], request.form['question'], user_id)
        question_id = data_manager.get_last_question_id()
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/add-tag', methods=['GET', 'POST'])
def add_tag_to_question(question_id=None):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if request.method == 'GET' and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        question = data_manager.get_question_by_id(question_id)  # add tag get
        question_title = question[0]['title']
        tags = data_manager.get_tags(question_id)
        return render_template('add_tag_head.html', question_title=question_title, tags=tags, question_id=question_id, user_id=user_id)
    elif request.method == 'POST' and user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        question = data_manager.get_question_by_id(question_id)
        question_id_to_add = question[0]['id']
        tag = request.form['new_tag']
        data_manager.add_tag_to_question(question_id_to_add, tag)
    else:  # not authorized to add tag
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/<int:tag_id>/delete-tag')
def delete_tag(question_id=None, tag_id=None):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        try:
            data_manager.delete_tag(question_id, tag_id)
        finally:
            return redirect('/question/{}'.format(question_id))
    else:
        flash('Invalid user')
        return redirect('/question/{}'.format(question_id))


@app.route('/answer/<answer_id>/delete')
def delete_answer(answer_id=None):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    question_id = data_manager.get_foreign_key_by_id(data_manager.answer_db, 'question_id', answer_id)[0]['question_id']
    if user_id == data_manager.get_foreign_key_by_id(data_manager.answer_db, 'users_id', answer_id)[0]['users_id']:
        data_manager.delete_line_by_foreign_id(data_manager.comment_db, 'answer_id', answer_id)
        question_id = data_manager.delete_answer_by_id(answer_id)['question_id']
        filename = 'static/image_for_answer' + str(answer_id) + '.png'
        if util.check_file(filename):
            util.delete_file(filename)
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/answer/<answer_id>/accept')
def accept_answer(answer_id):
    answer = data_manager.get_line_data_by_id(data_manager.answer_db, answer_id)
    question_users_id=data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', answer[0]['question_id'])[0]['users_id']
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if answer[0]['accepted_status'] is False and user_id == question_users_id:
        answer_statuses = list(map(lambda x: x['accepted_status'], data_manager.get_lines_data_by_foreign_id(data_manager.answer_db, 'question_id', answer[0]['question_id'])))
        if True not in answer_statuses:
            data_manager.accept_answer(answer_id)
        else:
            flash('You can only accept one answer')
    else:
        flash('Invalid user')
    user_id = data_manager.get_user_id_by_answer_id(answer_id)
    data_manager.increase_reputation('accept', user_id)
    question_id = data_manager.get_foreign_key_by_id(data_manager.answer_db, 'question_id', answer_id)[0]['question_id']
    return redirect('/question/{}'.format(question_id))


@app.route('/question/<int:question_id>/delete')
def delete_question(question_id=None):
    try:
        user_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    if user_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', question_id)[0]['users_id']:
        data_manager.delete_line_by_foreign_id(data_manager.comment_db, 'question_id', question_id)
        filename = 'static/image_for_question' + str(question_id) + '.png'
        if util.check_file(filename):
            util.delete_file(filename)
        answer_ids_to_delete = data_manager.get_ids_by_foreign_id(data_manager.answer_db, 'question_id', question_id)
        for answer_id in answer_ids_to_delete:
            data_manager.delete_line_by_foreign_id(data_manager.comment_db, 'answer_id', answer_id['id'])
            filename = 'static/image_for_answer' + str(answer_id['id']) + '.png'
            if util.check_file(filename):
                util.delete_file(filename)
        data_manager.delete_answer_by_question_id(question_id)
        data_manager.delete_question(question_id)
    else:
        flash('Invalid user')
    return redirect('/list')


@app.route('/question/<int:question_id>/<int:id>/<file_>/<method>')
def vote(question_id=None, id=None, file_=None, method=None):
    try:
        users_id = data_manager.get_userid_by_username(session['username'])
    except KeyError:
        return redirect('/')
    answers = data_manager.sort_table(data_manager.answer_db, 'id', 'asc')
    questions = data_manager.sort_table(data_manager.question_db, 'id', 'asc')
    voted_questions_of_user = list(map(lambda x: x['question_id'],
                                       data_manager.get_foreign_key_by_id(data_manager.user_vote_db, 'question_id',
                                                                          users_id)))
    voted_answers_of_user = list(map(lambda x: x['answer_id'],
                                     data_manager.get_foreign_key_by_id(data_manager.user_vote_db, 'answer_id',
                                                                        users_id)))
    if file_ == 'answer'\
            and not users_id == data_manager.get_foreign_key_by_id(data_manager.answer_db, 'users_id', id)[0]['users_id']\
            and answers[id-1]['id'] not in voted_answers_of_user:
        data_manager.change_vote_number_in_table(data_manager.answer_db, id, method)
        data_manager.add_vote_to_user_vote(None, id, users_id)
        user_id = data_manager.get_user_id_by_answer_id(id)
        if method == 'up':
            data_manager.increase_reputation('answer', user_id=user_id)
        elif method == 'down':
            data_manager.reduce_reputation(user_id=user_id)
    elif file_ == 'question'\
            and not users_id == data_manager.get_foreign_key_by_id(data_manager.question_db, 'users_id', id)[0]['users_id'] \
            and questions[id-1]['id'] not in voted_questions_of_user:
        data_manager.change_vote_number_in_table(data_manager.question_db, id, method)
        data_manager.add_vote_to_user_vote(id, None, users_id)
        user_id = data_manager.get_user_id_by_question_id(id)
        if method == 'up':
            data_manager.increase_reputation('question', user_id=user_id)
        elif method == 'down':
            data_manager.reduce_reputation(user_id=user_id)
    else:
        flash('Invalid user')
    return redirect('/question/{}'.format(question_id))


@app.route('/search', methods=['GET', 'POST'])
def search():
    user_id = data_manager.get_userid_by_username(session.get('username'))
    search_phrase = request.form['search_phrase']
    headers = data_manager.get_column_names_of_table(data_manager.question_db)
    questions = data_manager.search(search_phrase)
    answers = data_manager.search_answers(search_phrase)
    return render_template('search_results_head.html', questions=questions, answers=answers,
                           headers=headers, search_phrase=search_phrase, user_id=user_id)


@app.route('/registration', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('registration_head.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            data_manager.register_user(username, password)
            return redirect('/')
        except:
            invalid_username = 'Username is taken'
            return render_template('registration_head.html', invalid_username=invalid_username)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        good_hash_pw = data_manager.get_hashpw_of_username(request.form['username'])
        if good_hash_pw and util.verify_password(request.form['password'], good_hash_pw):
            session['username'] = request.form['username']
            return redirect('/')
        else:
            invalid_username_or_password = 'invalid username or password'
            return render_template('login_head.html', invalid_username_or_password=invalid_username_or_password)
    elif request.method == 'GET':
        return render_template('login_head.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')


@app.route('/tags')
def tag_page():
    user_id = data_manager.get_userid_by_username(session.get('username'))
    data = data_manager.get_tags_and_question_count()
    return render_template('all_tags_head.html', data=data, user_id=user_id)


@app.route('/tags/<string:tag_name>')
@app.route('/tags/<string:tag_name>/')
def get_qestions_by_tag(tag_name):
    user_id = data_manager.get_userid_by_username(session.get('username'))
    headers = data_manager.get_column_names_of_table(data_manager.question_db)
    questions = data_manager.get_questions_by_tag(tag_name)
    if request.args:
        questions = util.sort_list_of_table_rows(questions, request.args['order_by'],
                                            request.args['order_direction'])
    return render_template('questions_by_tag_head.html', questions=questions, headers=headers, tag_name=tag_name, user_id=user_id)




if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
