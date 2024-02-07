import os

import quizgen.variant
import quizgen.constants

import jinja2

TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_FILENAME_QUESTION_SEP = 'question-separator.template'

DEFAULT_JINJA_OPTIONS = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

class TemplateConverter(object):
    def __init__(self, format, template_dir, answer_key = False, jinja_options = {}, **kwargs):
        super().__init__()

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir
        self.answer_key = answer_key
        self.jinja_options = DEFAULT_JINJA_OPTIONS | jinja_options

        self.env = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.template_dir),
            **self.jinja_options,
        )

        # Methods to generate answers.
        # Signatuire: func(self, base_template (for an answer of this type), key_template (if exists) question_index, question)
        self.answer_functions = {
            quizgen.constants.QUESTION_TYPE_ESSAY: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_FIMB: 'create_answers_fimb',
            quizgen.constants.QUESTION_TYPE_FITB: 'create_answers_fitb',
            quizgen.constants.QUESTION_TYPE_MATCHING: 'create_answers_matching',
            quizgen.constants.QUESTION_TYPE_MA: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MCQ: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MDD: 'create_answers_mdd',
            quizgen.constants.QUESTION_TYPE_NUMERICAL: 'create_answers_numerical',
            quizgen.constants.QUESTION_TYPE_SA: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_TEXT_ONLY: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_TF: 'create_answers_list',
        }

    def convert_quiz(self, variant, **kwargs):
        if (not isinstance(variant, quizgen.variant.Variant)):
            raise ValueError("Template quiz converter requires a quizgen.quiz.Variant type, found %s." % (type(variant)))

        questions_text = self.create_questions(variant)

        variant_context = variant.to_dict(include_docs = False)
        variant_context['description_text'] = variant.description_document.to_format(self.format)

        context = {
            'quiz': variant_context,
            'answer_key': self.answer_key,
            'questions_text': questions_text,
        }

        variant_template = self.env.get_template(TEMPLATE_FILENAME_QUIZ)
        text = variant_template.render(**context)

        return text

    def create_questions(self, variant):
        questions = []

        question_number = 1
        for question_index in range(len(variant.questions)):
            question = variant.questions[question_index]

            if (question_index != 0):
                questions.append(self.create_question_separator(variant))

            questions.append(self.create_question(question_index, question_number, question, variant))

            if (not question.should_skip_numbering()):
                question_number += 1

            # TEST
            if (question_index >= 1):
                break

        return "\n\n".join(questions)

    def create_question(self, question_index, question_number, question, variant):
        data = question.to_dict(include_docs = False)
        data['prompt_text'] = question.prompt_document.to_format(self.format)
        data['id'] = question_index
        data['number'] = question_number

        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
            'question': data,
        }

        question_type = self.check_variable(question, 'question_type', label = 'Question')
        template_name = "%s.template" % (question_type)

        # TEST
        try:
            template = self.env.get_template(template_name)
            text = template.render(**context)
        except Exception as ex:
            import json
            print('---')
            print(json.dumps(question.to_dict(include_docs = False), indent = 4))
            print('---')

            raise ex

        return text

    def create_question_separator(self, variant):
        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUESTION_SEP)
        text = template.render(**context)

        return text

    # TEST
    def check_variable(self, source, name, label = "Object"):
        value = getattr(source, name, '')
        if ((value is None) or (value == '')):
            raise ValueError("%s is missing key value: '%s'." % (label, name))

        return value
