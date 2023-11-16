import glob
import json
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
            groups = [], **kwargs):
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

        self.validate()

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
        return Quiz(groups = groups, **quiz_info)

    def to_tex(self):
        # TEST
        groupsText = "\n".join([group.to_tex() for group in self.groups])

        replacements = {
            '%%title%%': self.title,
            '%%groups%%': groupsText,
        }

        text = LATEX_QUIZ_TEMPLATE

        for (key, value) in replacements.items():
            text = text.replace(key, value)

        return text

class Group(object):
    def __init__(self, name = '',
            pick_count = 1, question_points = 1, questions = [],
            **kwargs):
        self.name = name
        self.pick_count = pick_count
        self.question_points = question_points

        self.questions = questions

        self.validate()

    def validate(self):
        if ((self.name is None) or (self.name == "")):
            raise ValueError("Name cannot be empty.")

    def to_dict(self):
        value = self.__dict__.copy()
        value['questions'] = [question.to_dict() for question in self.questions]
        return value

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            group_info = json.load(file)

        questions = _parse_questions(os.path.dirname(path))
        return Group(questions = questions, **group_info)

    def to_tex(self):
        # TEST
        # TODO(eriq): Pick count is not honored.

        question = random.choice(self.questions)
        replacements = {
            '%%name%%': self.name,
            '%%question%%': question.to_tex(),

            ' \\n ': " \\\\ ",
        }

        text = LATEX_GROUP_TEMPLATE

        for (key, value) in replacements.items():
            text = text.replace(key, value)

        return text

class Question(object):
    def __init__(self, prompt = '', question_type = '', answers = [],
            base_dir = '.',
            **kwargs):
        self.prompt = prompt
        self.prompt_document = quizgen.parser.parse_text(self.prompt, base_dir = base_dir)

        self.question_type = question_type

        self.answers = answers
        for answer in self.answers:
            answer['document'] = quizgen.parser.parse_text(answer['text'], base_dir = base_dir)

        self.validate()

    def validate(self):
        if ((self.prompt is None) or (self.prompt == "")):
            raise ValueError("Prompt cannot be empty.")

        if (self.question_type not in quizgen.constants.QUESTION_TYPES):
            raise ValueError(f"Unknown question type: '{self.question_type}'.")

    def to_dict(self):
        value = self.__dict__.copy()

        value['prompt_document'] = self.prompt_document.to_pod()

        value['answers'] = []
        for answer in self.answers:
            answer = answer.copy()
            answer['document'] = answer['document'].to_pod()
            value['answers'].append(answer)

        return value

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            question_info = json.load(file)

        # Check for a prompt file.
        prompt_path = os.path.join(os.path.dirname(path), PROMPT_FILENAME)
        if (os.path.exists(prompt_path)):
            question_info['prompt'] = quizgen.util.file.read(prompt_path)

        base_dir = os.path.dirname(path)

        return Question(base_dir = base_dir, **question_info)

    def to_tex(self):
        # TEST
        answersText = "\n".join(["%s. %s" % (string.ascii_uppercase[i], self.answers[i]['text']) for i in range(len(self.answers))])

        replacements = {
            '%%prompt%%': self.prompt,
            '%%answers%%': answersText,

            ' \\n ': " \\\\ ",
        }

        text = LATEX_QUESTION_TEMPLATE

        for (key, value) in replacements.items():
            text = text.replace(key, value)

        return text

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
