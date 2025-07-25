"""
Download quiz informaion from Canvas.
"""

import json

import lms.api.quiz.fetch
import lms.api.quiz.question.fetch

import quizcomp.pandoc

def download_quiz(base_url, course_id, token, quiz_query):
    quiz_info = lms.api.quiz.fetch(server = base_url, course = course_id, token = token,
            quizzes = [quiz_query])

    # TEST
    print('---')
    print(json.dumps(quiz_info))
    print('---')


def download_quiz_question(base_url, course_id, token, quiz_query, question_query):
    question_info = lms.api.quiz.question.fetch.request(server = base_url, course = course_id, token = token,
            quiz = quiz_query, questions = [question_query])

    # TEST
    print('---')
    print(json.dumps(question_info))
    print('---')

    text = question_info[0]['question_text']

    markdown = quizcomp.pandoc.convert_string(text, 'html', 'gfm')

    # TEST
    print('###')
    print(markdown)
    print('###')
