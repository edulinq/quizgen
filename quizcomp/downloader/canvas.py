"""
Download quiz informaion from Canvas.
"""

import json

import lms.api.quiz.fetch
import lms.api.quiz.question.fetch

import quizcomp.pandoc
import quizcomp.question.sa

CANVAS_QUESTION_TYPE_ESSAY = 'essay_question'
CANVAS_QUESTION_TYPE_FIMB = 'fill_in_multiple_blanks_question'
CANVAS_QUESTION_TYPE_MATCHING = 'matching_question'
CANVAS_QUESTION_TYPE_MA = 'multiple_answers_question'
CANVAS_QUESTION_TYPE_MCQ = 'multiple_choice_question'
CANVAS_QUESTION_TYPE_MDD = 'multiple_dropdowns_question'
CANVAS_QUESTION_TYPE_NUMERICAL = 'numerical_question'
CANVAS_QUESTION_TYPE_TEXT_ONLY = 'text_only_question'
CANVAS_QUESTION_TYPE_TF = 'true_false_question'
CANVAS_QUESTION_TYPE_SA = 'short_answer_question'
CANVAS_QUESTION_TYPE_ESSAY = 'essay_question'

def download_quiz(base_url, course_id, token, quiz_query):
    quiz_info = lms.api.quiz.fetch(server = base_url, course = course_id, token = token,
            quizzes = [quiz_query])

    # TEST
    print('---')
    print(json.dumps(quiz_info))
    print('---')

def download_quiz_question(base_url, course_id, token, quiz_query, question_query):
    results = lms.api.quiz.question.fetch.request(server = base_url, course = course_id, token = token,
            quiz = quiz_query, questions = [question_query])
    if (len(results) != 1):
        raise ValueError(f"Did not find exactly one result matching quiz ('{quiz_query}') and question ('{question_query}'), found {len(results)} results.")

    return _convert_question(results[0])

def _convert_question(question_info):
    """ Create a lms.question.base.Question from the Canvas question info. """

    prompt = quizcomp.pandoc.convert_string(question_info['question_text'], 'html', 'gfm')

    base_info = {
        'prompt': prompt,
        'points': question_info.get('points_possible', 0),
        'name': question_info.get('question_name', ''),
    }

    question_type = question_info['question_type']
    if (question_type == CANVAS_QUESTION_TYPE_SA):
        question = quizcomp.question.sa.Essay(**base_info)
    else:
        raise ValueError(f"Unknown question type '{question_info['question_type']}'.")

    return question
