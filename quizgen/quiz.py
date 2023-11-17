import glob
import json
import math
import os
import random
import string

import quizgen.constants
import quizgen.parser
import quizgen.util.file

QUIZ_FILENAME = 'quiz.json'
GROUP_FILENAME = 'group.json'
QUESTION_FILENAME = 'question.json'
PROMPT_FILENAME = 'prompt.md'

class Quiz(object):
    def __init__(self, title = '', description = '',
            quiz_type = quizgen.constants.QUIZ_TYPE_PRACTICE, published = False,
            time_limit = 30, shuffle_answers = True,
            hide_results = None, show_correct_answers = True,
            assignment_group_name = "Quizzes",
            groups = [], path = None, **kwargs):
        self.title = title
        self.description = description
        self.quiz_type = quiz_type
        self.published = published
        self.time_limit = time_limit
        self.shuffle_answers = shuffle_answers
        self.hide_results = hide_results
        self.show_correct_answers = show_correct_answers
        self.assignment_group_name = assignment_group_name

        self.groups = groups

        try:
            self.validate()
        except Exception as ex:
            raise ValueError(f"Error while validating quiz: '{path}'.") from ex

    def validate(self):
        # TEST - More to validate, check all init params.

        if ((self.title is None) or (self.title == "")):
            raise ValueError("Title cannot be empty.")

        if ((self.description is None) or (self.description == "")):
            raise ValueError("Description cannot be empty.")

        if (self.quiz_type not in quizgen.constants.QUIZ_TYPES):
            raise ValueError(f"Unknown quiz type: '{self.quiz_type}'.")

    def to_dict(self):
        value = self.__dict__.copy()
        value['groups'] = [group.to_dict() for group in self.groups]
        return value

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            quiz_info = json.load(file)

        groups = _parse_groups(os.path.dirname(path))
        return Quiz(groups = groups, path = path, **quiz_info)

class Group(object):
    def __init__(self, name = '',
            pick_count = 1, question_points = 1,
            questions = [], path = None, **kwargs):
        self.name = name
        self.pick_count = pick_count
        self.question_points = question_points

        self.questions = questions

        try:
            self.validate()
        except Exception as ex:
            raise ValueError(f"Error while validating group: '{path}'.") from ex

    def validate(self):
        if ((self.name is None) or (self.name == "")):
            raise ValueError("Name cannot be empty.")

    def to_dict(self):
        value = self.__dict__.copy()
        value['questions'] = [question.to_dict() for question in self.questions]
        return value

    def collect_file_paths(self):
        paths = []

        for question in self.questions:
            paths += question.collect_file_paths()

        return paths

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            group_info = json.load(file)

        questions = _parse_questions(os.path.dirname(path))
        return Group(questions = questions, path = path, **group_info)

class Question(object):
    def __init__(self, prompt = '', question_type = '', answers = [],
            base_dir = '.', path = None,
            **kwargs):
        self.base_dir = base_dir

        self.prompt = prompt
        self.prompt_document = quizgen.parser.parse_text(self.prompt, base_dir = self.base_dir)

        self.question_type = question_type
        self.answers = answers

        try:
            self.validate()
        except Exception as ex:
            raise ValueError(f"Error while validating question: '{path}'.") from ex

    def validate(self):
        if ((self.prompt is None) or (self.prompt == "")):
            raise ValueError("Prompt cannot be empty.")

        if (self.question_type not in quizgen.constants.QUESTION_TYPES):
            raise ValueError(f"Unknown question type: '{self.question_type}'.")

        self._validate_answers()

    def _validate_answers(self):
        if (self.question_type == quizgen.constants.QUESTION_TYPE_MULTIPLE_CHOICE):
            self._validate_answer_list(self.answers, min_correct = 1, max_correct = 1)
        elif (self.question_type == quizgen.constants.QUESTION_TYPE_MULTIPLE_ANSWERS):
            self._validate_answer_list(self.answers)
        elif (self.question_type == quizgen.constants.QUESTION_TYPE_MULTIPLE_DROPDOWNS):
            for answers in self.answers.values():
                self._validate_answer_list(answers, min_correct = 1, max_correct = 1)
        elif (self.question_type == quizgen.constants.QUESTION_TYPE_TF):
            self._validate_tf_answers()
        elif (self.question_type == quizgen.constants.QUESTION_TYPE_MATCHING):
            self._validate_matching_answers()
        else:
            raise ValueError(f"Unknown question type: '{self.question_type}'.")

    def _validate_tf_answers(self):
        if (not isinstance(self.answers, bool)):
            raise ValueError(f"'answers' for a T/F question must be a boolean, found '{self.answers}' ({type(self.answers)}).")

        # Change answers to look like multiple choice.
        self.answers = [
            {"correct": self.answers, "text": 'True'},
            {"correct": (not self.answers), "text": 'False'},
        ]

        self._validate_answer_list(self.answers)

    def _validate_matching_answers(self):
        if (not isinstance(self.answers, dict)):
            raise ValueError(f"Expected dict for matching answers, found {type(self.answers)}.")

        if ('matches' not in self.answers):
            raise ValueError("Matching answer type is missing the 'matches' field.")

        for match in self.answers['matches']:
            if (len(match) != 2):
                raise ValueError(f"Expected exactly two items for a match list, found {len(match)}.")

        if ('distractors' not in self.answers):
            self.answers['distractors'] = []

        for distractor in self.answers['distractors']:
            if (not isinstance(distractor, str)):
                raise ValueError(f"Distractors must be strings, found {type(distractor)}.")

    def _validate_answer_list(self, answers, min_correct = 0, max_correct = math.inf):
        if (not isinstance(answers, list)):
            raise ValueError(f"Expected answers to be a list, found {type(answers)} (base_dir: '{self.base_dir}'.")

        num_correct = 0
        for answer in answers:
            self._validate_answer(answer)
            if (answer['correct']):
                num_correct += 1

        if (num_correct < min_correct):
            raise ValueError(f"Did not find enough correct answers. Expected at least {min_correct}, found {num_correct} (base_dir: '{self.base_dir}'.")

        if (num_correct > max_correct):
            raise ValueError(f"Found too many correct answers. Expected at most {max_correct}, found {num_correct} (base_dir: '{self.base_dir}'.")

    def _validate_answer(self, answer):
        if ('correct' not in answer):
            raise ValueError(f"Answer has no 'correct' field (base_dir: '{self.base_dir}'.")

        if ('text' not in answer):
            raise ValueError(f"Answer has no 'text' field (base_dir: '{self.base_dir}'.")

        answer['document'] = quizgen.parser.parse_text(answer['text'], base_dir = self.base_dir)

    def to_dict(self):
        value = self.__dict__.copy()

        value['prompt_document'] = self.prompt_document.to_pod()
        value['answers'] = self._answers_to_dict(self.answers)

        return value

    def _answers_to_dict(self, target):
        if (isinstance(target, dict)):
            return {key: self._answers_to_dict(value) for (key, value) in target.items()}
        elif (isinstance(target, list)):
            return [self._answers_to_dict(answer) for answer in target]
        elif (isinstance(target, quizgen.parser.ParseNode)):
            return target.to_pod()
        else:
            return target

    def collect_file_paths(self):
        paths = []

        paths += self.prompt_document.collect_file_paths(self.base_dir)

        for document in self._collect_documents(self.answers):
            paths += document.collect_file_paths(self.base_dir)

        return paths

    def _collect_documents(self, target):
        if (isinstance(target, dict)):
            return self._collect_documents(list(target.values()))
        elif (isinstance(target, list)):
            documents = []
            for value in target:
                documents += self._collect_documents(value)
            return documents
        elif (isinstance(target, quizgen.parser.ParseNode)):
            return [target]
        else:
            return []

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            question_info = json.load(file)

        # Check for a prompt file.
        prompt_path = os.path.join(os.path.dirname(path), PROMPT_FILENAME)
        if (os.path.exists(prompt_path)):
            question_info['prompt'] = quizgen.util.file.read(prompt_path)

        base_dir = os.path.dirname(path)

        return Question(base_dir = base_dir, path = path, **question_info)

def _parse_questions(base_dir):
    questions = []
    for path in sorted(glob.glob(os.path.join(base_dir, '**', QUESTION_FILENAME), recursive = True)):
        questions.append(Question.from_path(path))

    return questions

def _parse_groups(base_dir):
    groups = []
    for path in sorted(glob.glob(os.path.join(base_dir, '**', GROUP_FILENAME), recursive = True)):
        groups.append(Group.from_path(path))

    return groups

def parse_quiz_dir(basedir):
    quizzes = []

    for path in sorted(glob.glob(os.path.join(basedir, '**', QUIZ_FILENAME), recursive = True)):
        quizzes.append(Quiz.from_path(path))

    return quizzes

LATEX_QUIZ_TEMPLATE = r"""
    \documentclass{exam}

    \title{%%title%%}

    \begin{document}

        \maketitle

        \begin{center}
            \fbox{\fbox{\parbox{5.5in}{\centering
                Answer the questions in the spaces provided.
                If you run out of room for an answer, continue on the back of the page.
            }}}
        \end{center}

        \vspace{5mm}
        \makebox[0.75\textwidth]{Name:\enspace\hrulefill}

        \vspace{5mm}
        \makebox[0.75\textwidth]{CruzID:\enspace\hrulefill}

        \begin{questions}

            %%groups%%

        \end{questions}
    \end{document}
"""

LATEX_GROUP_TEMPLATE = r"""
    \question
    %%name%%

    %%question%%

"""

LATEX_QUESTION_TEMPLATE = r"""
    %%prompt%%
    \\
    %%answers%%
"""
