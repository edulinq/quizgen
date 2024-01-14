DOC_FORMAT_GRADESCOPE = 'gradescope'
DOC_FORMAT_HTML = 'html'
DOC_FORMAT_JSON = 'json'
DOC_FORMAT_MD = 'md'
DOC_FORMAT_TEX = 'tex'
DOC_FORMAT_TEXT = 'text'

# Output formats.
DOC_FORMATS = [DOC_FORMAT_GRADESCOPE, DOC_FORMAT_HTML, DOC_FORMAT_JSON, DOC_FORMAT_MD, DOC_FORMAT_TEX, DOC_FORMAT_TEXT]

# Formats that the parser understands basic conversions to.
PARSER_FORMATS = [DOC_FORMAT_HTML, DOC_FORMAT_JSON, DOC_FORMAT_MD, DOC_FORMAT_TEX, DOC_FORMAT_TEXT]

QUIZ_TYPE_PRACTICE = 'practice_quiz'
QUIZ_TYPE_ASSIGNMENT = 'assignment'
QUIZ_TYPE_GRADED_SURVEY = 'graded_survey'
QUIZ_TYPE_SURVEY = 'survey'
QUIZ_TYPES = [QUIZ_TYPE_PRACTICE, QUIZ_TYPE_ASSIGNMENT, QUIZ_TYPE_GRADED_SURVEY, QUIZ_TYPE_SURVEY]

# All question types Canvas supports.
QUESTION_TYPE_CALCULATED = 'calculated_question'
QUESTION_TYPE_ESSAY = 'essay_question'
QUESTION_TYPE_FILE_UPLOAD = 'file_upload_question'
QUESTION_TYPE_FIMB = 'fill_in_multiple_blanks_question'
QUESTION_TYPE_MATCHING = 'matching_question'
QUESTION_TYPE_MA = 'multiple_answers_question'
QUESTION_TYPE_MCQ = 'multiple_choice_question'
QUESTION_TYPE_MDD = 'multiple_dropdowns_question'
QUESTION_TYPE_NUMERICAL = 'numerical_question'
QUESTION_TYPE_TEXT_ONLY = 'text_only_question'
QUESTION_TYPE_TF = 'true_false_question'

# QuizGen Special Question Types

# Canvas has a type of question that uses a single text box at the end which is matches against a text answer.
# They cann this question type both "Fill in the Blank" and "Short Answer".
# In QuizGen, we cann this type "Fill in the Blank",
# whereas "Short Answer" will be a type with an undefined answer but less reserved space than "Essay" questions.
QUESTION_TYPE_FITB = 'fill_in_the_blank_question'
QUESTION_TYPE_SA = 'short_answer_question'

# Supported question types.
QUESTION_TYPES = [
    QUESTION_TYPE_ESSAY,
    QUESTION_TYPE_FIMB,
    QUESTION_TYPE_FITB,
    QUESTION_TYPE_MATCHING,
    QUESTION_TYPE_MA,
    QUESTION_TYPE_MCQ,
    QUESTION_TYPE_MDD,
    QUESTION_TYPE_NUMERICAL,
    QUESTION_TYPE_SA,
    QUESTION_TYPE_TEXT_ONLY,
    QUESTION_TYPE_TF,
]

NUMERICAL_ANSWER_TYPE_EXACT = 'exact'
NUMERICAL_ANSWER_TYPE_RANGE = 'range'
NUMERICAL_ANSWER_TYPE_PRECISION = 'precision'
