#!/usr/bin/env python3

import re

import requests

# TODO(eriq): This code assumes there will never be more than a page of items returned.
PAGE_SIZE = 75

# TODO - Need to get assignment_group_id from name.
# TODO - Hide REsults ('hide_results') - 'always', 'until_after_last_attempt', None

# TODO(eriq): Put in a force paramater to avoid overwriting existing quizes.

# TODO(eriq): Logging.

def upload_quiz(quiz, base_url, course_id, token):
    existing_ids = get_matching_quiz_ids(quiz.title, base_url, course_id, token)
    for existing_id in existing_ids:
        delete_quiz(existing_id, base_url, course_id, token)

    create_quiz(quiz, base_url, course_id, token)

def base_headers(token):
    return {
        "Authorization": "Bearer %s" % (token),
        "Accept": "application/json+canvas-string-ids",
    }

def get_matching_quiz_ids(title, base_url, course_id, token):
    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/quizzes?per_page=%d" % (base_url, course_id, PAGE_SIZE),
        headers = base_headers(token))
    response.raise_for_status()

    ids = []
    for quiz in response.json():
        if (quiz['title'] == title):
            ids.append(quiz['id'])

    return ids

def delete_quiz(quiz_id, base_url, course_id, token):
    response = requests.request(
        method = "DELETE",
        url = "%s/api/v1/courses/%s/quizzes/%s" % (base_url, course_id, quiz_id),
        headers = base_headers(token))
    response.raise_for_status()

def fetch_assignment_group(name, base_url, course_id, token):
    if (name is None):
        return None

    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/assignment_groups?per_page=%d" % (base_url, course_id, PAGE_SIZE),
        headers = base_headers(token))
    response.raise_for_status()

    for assignment in response.json():
        if (assignment['name'] == name):
            return assignment['id']

    return None

def create_quiz(quiz, base_url, course_id, token):
    assignment_group_id = fetch_assignment_group(quiz.assignment_group_name, base_url, course_id, token)

    create_info = {
        'quiz[title]': quiz.title,
        'quiz[description]': quiz.description,
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
        url = "%s/api/v1/courses/%s/quizzes" % (base_url, course_id),
        headers = base_headers(token),
        data = create_info)
    response.raise_for_status()

    quiz_id = response.json()['id']

    for question_group in quiz.groups:
        create_question_group(quiz_id, question_group, base_url, course_id, token)

def create_question_group(quiz_id, group, base_url, course_id, token):
    create_info = {
        'quiz_groups[][name]': group.name,
        'quiz_groups[][pick_count]': group.pick_count,
        'quiz_groups[][question_points]': group.question_points,
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/groups" % (base_url, course_id, quiz_id),
        headers = base_headers(token),
        data = create_info)
    response.raise_for_status()

    group_id = response.json()['quiz_groups'][0]['id']

    for i in range(len(group.questions)):
        create_question(quiz_id, group_id, group.questions[i], i, base_url, course_id, token)

def create_question(quiz_id, group_id, question, index, base_url, course_id, token):
    create_info = {
        'question[question_type]': question.question_type,
        'question[quiz_group_id]': group_id,
        'question[position]': index,
        'question[question_text]': question.prompt_document.to_html(),
    }

    for i in range(len(question.answers)):
        weight = 0
        if (question.answers[i]['correct']):
            weight = 100

        create_info["question[answers][%d][answer_weight]" % (i)] = weight

        html = question.answers[i]['document'].to_html()
        create_info["question[answers][%d][answer_html]" % (i)] = html

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/questions" % (base_url, course_id, quiz_id),
        headers = base_headers(token),
        data = create_info)
    response.raise_for_status()
