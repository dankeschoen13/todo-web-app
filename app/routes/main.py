from flask import Blueprint, render_template, request
from flask_login import current_user
from app.services import ListSvc


main_bp = Blueprint('main', __name__)


@main_bp.get('/')
def index():
    user_lists = current_user.authored_lists
    return render_template(
        'index.html',
        user_lists=user_lists
    )


# List Routes
@main_bp.post('/api/new-list')
def create_list():
    data = request.get_json()
    title = data.get('title')

    try:
        new_list = ListSvc.create_list(current_user, title)
        return render_template(
            'components/task-list.html',
            todo_list=new_list,
        )
    except ValueError as e:
        return {"error": str(e)}, 400

@main_bp.patch('/api/lists/<int:list_id>/title')
def edit_list(list_id):
    data = request.get_json()
    new_title = data.get('title')

    try:
        ListSvc.update_list(list_id, new_title)

    except ValueError as e:
        return {"error": str(e)}, 400

    return "", 204

@main_bp.delete('/api/lists/<int:list_id>/delete')
def delete_list(list_id):
    try:
        ListSvc.delete_list(list_id)
    except ValueError as e:
        return {"error": str(e)}, 400
    return "", 204


# Task Routes
@main_bp.post('/api/lists/<int:list_id>/task')
def create_task(list_id):
    data = request.get_json()
    content = data.get('content')

    try:
        new_task = ListSvc.create_task(current_user, list_id, content)
        return render_template(
            'components/task-item.html',
            task=new_task,
        )
    except ValueError as e:
        return {"error": str(e)}, 400

@main_bp.patch('/api/task/<int:task_id>/toggle')
def complete_task(task_id):
    try:
        ListSvc.complete_task(task_id)
    except ValueError as e:
        return {"error": str(e)}, 400
    return "", 204

@main_bp.delete('/api/task/<int:task_id>/delete')
def delete_task(task_id):
    try:
        ListSvc.delete_task(task_id)
    except ValueError as e:
        return {"error": str(e)}, 400
    return "", 204