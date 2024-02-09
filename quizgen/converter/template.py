import math
import os
import random
import string

import quizgen.constants
import quizgen.converter.converter
import quizgen.parser
import quizgen.variant

import jinja2

TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_FILENAME_QUESTION_SEP = 'question-separator.template'

RIGHT_IDS = string.ascii_uppercase
LEFT_IDS = [str(i + 1) for i in range(len(RIGHT_IDS))]

DEFAULT_JINJA_OPTIONS = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

class TemplateConverter(quizgen.converter.converter.Converter):
    def __init__(self, format, template_dir, jinja_options = {}, **kwargs):
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir

        self.jinja_options = DEFAULT_JINJA_OPTIONS.copy()
        self.jinja_options.update(jinja_options)

        self.env = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.template_dir, followlinks = True),
            **self.jinja_options,
        )

        # Methods to generate answers.
        # Signatuire: func(self, question_index, question_number, question, variant)
        self.answer_functions = {
            quizgen.constants.QUESTION_TYPE_ESSAY: 'create_answers_essay',
            quizgen.constants.QUESTION_TYPE_FIMB: 'create_answers_fimb',
            quizgen.constants.QUESTION_TYPE_FITB: 'create_answers_fitb',
            quizgen.constants.QUESTION_TYPE_MA: 'create_answers_ma',
            quizgen.constants.QUESTION_TYPE_MATCHING: 'create_answers_matching',
            quizgen.constants.QUESTION_TYPE_MCQ: 'create_answers_mcq',
            quizgen.constants.QUESTION_TYPE_MDD: 'create_answers_mdd',
            quizgen.constants.QUESTION_TYPE_NUMERICAL: 'create_answers_numerical',
            quizgen.constants.QUESTION_TYPE_SA: 'create_answers_sa',
            quizgen.constants.QUESTION_TYPE_TEXT_ONLY: 'create_answers_text_only',
            quizgen.constants.QUESTION_TYPE_TF: 'create_answers_tf',
        }

    def convert_variant(self, variant, **kwargs):
        if (not isinstance(variant, quizgen.variant.Variant)):
            raise ValueError("Template quiz converter requires a quizgen.variant.Variant type, found %s." % (type(variant)))

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

            try:
                questions.append(self.create_question(question_index, question_number, question, variant))
            except Exception as ex:
                raise ValueError("Failed to convert question %d (%s)." % (question_index, question.base_name)) from ex

            if (not question.should_skip_numbering()):
                question_number += 1

        return "\n\n".join(questions)

    def create_question(self, question_index, question_number, question, variant):
        question_type = question.question_type
        if (question_type not in self.answer_functions):
            raise ValueError("Unsupported question type: '%s'." % (question_type))

        data = question.to_dict(include_docs = False)
        data['prompt_text'] = question.prompt_document.to_format(self.format)
        data['id'] = question_index
        data['number'] = question_number

        # Stash the old answers and add in new ones.
        data['answers_raw'] = data['answers']
        answers_method = getattr(self, self.answer_functions[question_type])
        data['answers'] = answers_method(question_index, question_number, question, variant)

        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
            'question': data,
        }

        template_name = "%s.template" % (question_type)
        template = self.env.get_template(template_name)
        text = template.render(**context)

        return text

    def clean_solution_content(self, document):
        """
        An opportunity for children to clean the text of a solution before it is entered into a key.
        For example, tex solutions are hacky and cannot use certain functions.
        """

        return document.to_format(self.format)

    def create_question_separator(self, variant):
        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUESTION_SEP)
        text = template.render(**context)

        return text

    def create_answers_sa(self, question_index, question_number, question, variant):
        return None

    def create_answers_tf(self, question_index, question_number, question, variant):
        return question.answers

    def create_answers_matching(self, question_index, question_number, question, variant):
        lefts = []
        rights = []

        # {left_index: right_index, ...}
        matches = {}

        for (left, right) in question.answers_documents['matches']:
            matches[len(lefts)] = len(rights)

            lefts.append(left.to_format(self.format))
            rights.append(right.to_format(self.format))

        for right in question.answers_documents['distractors']:
            rights.append(right.to_format(self.format))

        left_ids = self.get_matching_left_ids()
        right_ids = self.get_matching_right_ids()

        if (len(lefts) > len(left_ids)):
            raise ValueError("Too many left-hand values for a matching question. Found: %d, Max %d." % (len(lefts) > len(left_ids)))

        if (len(rights) > len(right_ids)):
            raise ValueError("Too many right-hand values for a matching question. Found: %d, Max %d." % (len(rights) > len(right_ids)))

        if (question.answers.get('shuffle', False)):
            seed = question.answers.get('shuffle_seed', None)
            rng = random.Random(seed)

            # Shuffle the left and right options while maintining the match mapping.
            left_indexes = list(range(len(lefts)))
            right_indexes = list(range(len(rights)))

            rng.shuffle(left_indexes)
            rng.shuffle(right_indexes)

            new_lefts = [lefts[index] for index in left_indexes]
            lefts = new_lefts

            new_rights = [rights[index] for index in right_indexes]
            rights = new_rights

            new_matches = {left_indexes.index(old_left_index): right_indexes.index(old_right_index) for (old_left_index, old_right_index) in matches.items()}
            matches = new_matches

        # Augment the left and rights with more information for the template.
        for left_index in range(len(lefts)):
            right_index = matches[left_index]

            lefts[left_index] = {
                'id': "%d.%s" % (question_index, left_ids[left_index]),
                'text': lefts[left_index],
                'solution': right_ids[right_index],
                'solution_id': "%d.%s" % (question_index, right_ids[right_index]),
            }

        for right_index in range(len(rights)):
            rights[right_index] = {
                'id': "%d.%s" % (question_index, right_ids[right_index]),
                'text': rights[right_index],
                'label': right_ids[right_index],
            }

        return {
            'lefts': lefts,
            'rights': rights,
            'matches': matches,
        }

    def get_matching_left_ids(self):
        return LEFT_IDS

    def get_matching_right_ids(self):
        return RIGHT_IDS

    def create_answers_mcq(self, question_index, question_number, question, variant):
        return self._create_answers_mcq_list(question.answers, question.answers_documents)

    def _create_answers_mcq_list(self, answers, documents):
        choices = []

        for i in range(len(answers)):
            choices.append({
                'correct': answers[i]['correct'],
                'text': documents[i].to_format(self.format),
            })

        return choices

    def create_answers_text_only(self, question_index, question_number, question, variant):
        return None

    def create_answers_numerical(self, question_index, question_number, question, variant):
        answer = question.answers[0]

        if (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_EXACT):
            if (math.isclose(answer['margin'], 0.0)):
                content = "%s" % (str(answer['value']))
            else:
                content = "%s ± %f" % (str(answer['value']), answer['margin'])
        elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
            content = "[%s, %s]" % (str(answer['min']), str(answer['max']))
        elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_RANGE):
            content = "%s (precision: %s)" % (str(answer['value']), str(answer['precision']))
            raise ValueError(f"Unknown numerical answer type: '{answer['type']}'.")

        document = quizgen.parser.parse_text(content)

        return {
            'solution': self.clean_solution_content(document),
            'dirty_solution': document.to_format(self.format),
        }

    def create_answers_mdd(self, question_index, question_number, question, variant):
        answers = []

        for key, values in question.answers.items():
            answers.append({
                'label': question.answers_documents[key]['key'].to_format(self.format),
                'choices': self._create_answers_mcq_list(values, question.answers_documents[key]['values']),
            })

        return answers

    def create_answers_ma(self, question_index, question_number, question, variant):
        return self._create_answers_mcq_list(question.answers, question.answers_documents)

    def create_answers_fimb(self, question_index, question_number, question, variant):
        answers = []

        for key, values in question.answers.items():
            document = question.answers_documents[key]['values'][0]

            answers.append({
                'label': question.answers_documents[key]['key'].to_format(self.format),
                'solution': self.clean_solution_content(document),
                'dirty_solution': document.to_format(self.format),
            })

        return answers

    def create_answers_fitb(self, question_index, question_number, question, variant):
        document = question.answers_documents[""]["values"][0]

        return {
            'solution': self.clean_solution_content(document),
            'dirty_solution': document.to_format(self.format),
        }

    def create_answers_essay(self, question_index, question_number, question, variant):
        return None
