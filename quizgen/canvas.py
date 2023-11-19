#!/usr/bin/env python3

import os
import urllib.parse
import re

import requests

import quizgen.util.hash

# TODO(eriq): This code assumes there will never be more than a page of items returned.
PAGE_SIZE = 75

# TODO(eriq): Put in a force paramater to avoid overwriting existing quizes.

# TODO(eriq): Logging.

CANVAS_QUIZGEN_BASEDIR = '/quiz-generator'
CANVAS_QUIZGEN_QUIZ_DIRNAME = 'quiz'

class InstanceInfo(object):
    def __init__(self, base_url, course_id, token):
        self.base_url = base_url
        self.course_id = course_id
        self.token = token

        self.context = {}

    def base_headers(self):
        return {
            "Authorization": "Bearer %s" % (self.token),
            "Accept": "application/json+canvas-string-ids",
        }

def upload_quiz(quiz, instance):
    """
    Data may be written into the instance context.
    """

    existing_ids = get_matching_quiz_ids(quiz.title, instance)
    for existing_id in existing_ids:
        delete_quiz(existing_id, instance)

    create_quiz(quiz, instance)

def upload_canvas_files(quiz, instance):
    """
    Canvas requires that images (and other files) be uploaded to their side (instead of embedded),
    so upload all images in one method so we don't upload duplicates.
    """

    # {path: <canvas file id>, ...}
    file_ids = {}

    paths = []
    for group in quiz.groups:
        paths += group.collect_file_paths()

    paths = set(paths)

    for path in paths:
        canvas_path = '/'.join([
            CANVAS_QUIZGEN_BASEDIR,
            CANVAS_QUIZGEN_QUIZ_DIRNAME,
            quiz.title,
            quizgen.util.hash.sha256(path) + os.path.splitext(path)[-1]
        ])

        file_id = quizgen.canvas.upload_file(path, canvas_path, instance)
        file_ids[path] = file_id


    return file_ids

def get_matching_quiz_ids(title, instance):
    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/quizzes?per_page=%d" % (instance.base_url, instance.course_id, PAGE_SIZE),
        headers = instance.base_headers())
    response.raise_for_status()

    ids = []
    for quiz in response.json():
        if (quiz['title'] == title):
            ids.append(quiz['id'])

    return ids

def delete_quiz(quiz_id, instance):
    response = requests.request(
        method = "DELETE",
        url = "%s/api/v1/courses/%s/quizzes/%s" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers())
    response.raise_for_status()

def fetch_assignment_group(name, instance):
    if (name is None):
        return None

    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/assignment_groups?per_page=%d" % (instance.base_url, instance.course_id, PAGE_SIZE),
        headers = instance.base_headers())
    response.raise_for_status()

    for assignment in response.json():
        if (assignment['name'] == name):
            return assignment['id']

    return None

def create_quiz(quiz, instance):
    file_ids = upload_canvas_files(quiz, instance)
    instance.context['file_ids'] = file_ids

    assignment_group_id = fetch_assignment_group(quiz.assignment_group_name, instance)

    data = {
        'quiz[title]': quiz.title,
        'quiz[description]': f"<p>{quiz.description}</p><br /><hr /><p>Version: {quiz.version}</p>",
        'quiz[quiz_type]': quiz.quiz_type,
        'quiz[published]': quiz.published,
        'quiz[assignment_group_id]': assignment_group_id,
        'quiz[time_limit]': quiz.time_limit,
        'quiz[shuffle_answers]': quiz.shuffle_answers,
        'quiz[hide_results]': quiz.hide_results,
        'quiz[show_correct_answers]': quiz.show_correct_answers,
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    quiz_id = response.json()['id']

    for question_group in quiz.groups:
        create_question_group(quiz_id, question_group, instance)

def create_question_group(quiz_id, group, instance):
    data = {
        'quiz_groups[][name]': group.name,
        'quiz_groups[][pick_count]': group.pick_count,
        'quiz_groups[][question_points]': group.question_points,
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/groups" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    group_id = response.json()['quiz_groups'][0]['id']

    for i in range(len(group.questions)):
        create_question(quiz_id, group_id, group.questions[i], i, instance)

def create_question(quiz_id, group_id, question, index, instance):
    data = {
        'question[question_type]': question.question_type,
        'question[quiz_group_id]': group_id,
        'question[position]': index,
        'question[question_text]': question.prompt_document.to_html(canvas_instance = instance),
    }

    _serialize_answers(data, question, instance)

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/questions" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

def _serialize_answers(data, question, instance):
    if (question.question_type == quizgen.constants.QUESTION_TYPE_MATCHING):
        _serialize_matching_answers(data, question.answers, instance)
    elif (isinstance(question.answers, list)):
        use_text = (question.question_type == quizgen.constants.QUESTION_TYPE_TF)
        _serialize_answer_list(data, question.answers, instance, use_text = use_text)
    elif (isinstance(question.answers, dict)):
        count = 0
        for key, value in question.answers.items():
            _serialize_answer_list(data, value, instance,
                    start_index = count, blank_id = key, use_text = True)
            count += len(value)
    else:
        raise ValueError(f"Unknown answers type '{type(question.answers)}'.")

def _serialize_answer_list(data, answers, instance,
        start_index = 0, blank_id = None, use_text = False):
    for i in range(len(answers)):
        _serialize_answer(data, answers[i], start_index + i, instance,
            blank_id = blank_id, use_text = use_text)

def _serialize_answer(data, answer, index, instance, blank_id = None, use_text = False):
    weight = 0
    if (answer['correct']):
        weight = 100

    data["question[answers][%d][answer_weight]" % (index)] = weight

    if (use_text):
        text = answer['text']
        data["question[answers][%d][answer_text]" % (index)] = text
    else:
        html = answer['document'].to_html(canvas_instance = instance)
        data["question[answers][%d][answer_html]" % (index)] = html

    if (blank_id is not None):
        data["question[answers][%d][blank_id]" % (index)] = blank_id

def _serialize_matching_answers(data, answers, instance):
    right_contents = []

    for (_, right_text) in answers['matches']:
        right_contents.append(right_text)

    for right_text in answers['distractors']:
        right_contents.append(right_text)

    for i in range(len(answers['matches'])):
        left_content = answers['matches'][i][0]
        right_content = answers['matches'][i][1]

        data["question[answers][%d][answer_match_left]" % (i)] = left_content
        data["question[answers][%d][answer_match_right]" % (i)] = right_content

    if (len(answers['distractors']) > 0):
        data["question[matching_answer_incorrect_matches]"] = "\n".join(answers['distractors'])

def upload_file(path, canvas_path, instance):
    parent_id = ensure_folder(os.path.dirname(canvas_path), instance)
    upload_url, upload_params = _init_file_upload(path, canvas_path, parent_id, instance)
    file_id = _upload_file_contents(path, upload_url, upload_params)

    return file_id

def _init_file_upload(path, canvas_path, parent_id, instance):
    canvas_name = os.path.basename(canvas_path)

    size = os.stat(path).st_size

    data = {
        'name': canvas_name,
        'size': size,
        'parent_folder_id': parent_id,
        'on_duplicate': 'overwrite',
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/files" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    response = response.json()

    upload_url = response['upload_url']
    upload_params = response['upload_params']

    return upload_url, upload_params

def _upload_file_contents(path, upload_url, upload_params):
    files = {
        'file': open(path, 'rb'),
    }

    response = requests.request(
        method = "POST",
        url = upload_url,
        data = upload_params,
        files = files)
    response.raise_for_status()

    location = response.headers.get('Location', None)
    if (location is None):
        raise ValueError(f"Could not find location for uploaded file: '{path}'.")

    file_id = os.path.basename(urllib.parse.urlparse(location).path)

    return file_id

def ensure_folder(canvas_path, instance):
    folder_id = get_folder(canvas_path, instance)
    if (folder_id is not None):
        return folder_id

    folder_id = create_folder(canvas_path, instance)

    # Canvas will not hide created parents.
    hide_folder(CANVAS_QUIZGEN_BASEDIR, instance)

    return folder_id

def get_folder(canvas_path, instance):
    # The canvas path should be absolute.
    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/folders/by_path%s" % (instance.base_url, instance.course_id, canvas_path),
        headers = instance.base_headers())

    if (response.status_code == 404):
        return None

    response.raise_for_status()

    return response.json()[-1]['id']

def create_folder(canvas_path, instance):
    name = os.path.basename(canvas_path)
    parent_path = os.path.dirname(canvas_path)

    data = {
        'name': name,
        'parent_folder_path': parent_path,
        # Canvas wants a string here despite the documentation saying it is a bool.
        'hidden': 'true',
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/folders" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    folder_id = response.json()['id']

    return folder_id

def hide_folder(canvas_path, instance):
    folder_id = get_folder(canvas_path, instance)
    return hide_folder_id(folder_id, instance)

def hide_folder_id(folder_id, instance):
    data = {
        # Canvas wants a string here despite the documentation saying it is a bool.
        # TODO(eriq): Make a bug request?
        'hidden': 'true',
    }

    response = requests.request(
        method = "PUT",
        url = "%s/api/v1/folders/%s" % (instance.base_url, folder_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()
