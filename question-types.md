# Quiz Generator Question Types

The Quiz Generator (QuizGen) supports several different types of questions

Table of Contents:
 - [Data Types](#data-types)
 - [Common Fields](#common-fields)
 - [Question Types](#question-types)
   - [Multiple Choice (MC)](#multiple-choice-mc)
   - [True-False (TF)](#true-false-tf)
   - [Multiple Drop-Downs (MDD)](#multiple-drop-downs-mdd)
   - [Multiple Answers (MA)](#multiple-answers-ma)
   - [Matching](#matching)
   - [Fill in the Blank (FITB)](#fill-in-the-blank-fitb)
   - [Fill in Multiple Blanks (FIMB)](#fill-in-multiple-blanks-fimb)
   - [Numeric](#numeric)
   - [Short Answer (SA)](#short-answer-sa)
   - [Essay Questions](#essay-questions)
   - [Text-Only](#text-only)
 - [Differences with Canvas](#differences-with-canvas)

## Data Types

Since the QuizGen config is based around [JSON](https://en.wikipedia.org/wiki/JSON),
most data types used by the QuizGen are [simple JSON types](https://en.wikipedia.org/wiki/JSON#Data_types)
(ints, floats, strings, booleans, arrays/lists, objects (dicts/maps), and nulls).

The only difference between vanilla JSON types and QuizGen types is around the handling of strings.
The QuizGen divides strings into two types: plain strings and parsed strings.

Plain strings are limited to alphanumeric characters, spaces, underscores, and dashes.
These strings will often be used as keys (e.g., in Canvas options)
or as identifiers in some output language (e.g., as an HTML class).
Therefore, the content in plain strings are very limited.

Parsed strings are text that will be parsed by the QuizGen parser
(see [the syntax documentation](/syntax.md)),
and therefore must be valid syntax.
When using some output formats (like Canvas),
it may seem odd why some fields need to be parsed (like a question's title).
However, remember that some output formats (like TeX) will need to parse a question's title to produce valid TeX.

## Common Fields

Here are common fields that all question types share.
Some fields will be inherited from the group the question is located in,
if not set explicitly.

| Key               | Type          | Inherited? | Usage |
|-------------------|---------------|------------|-------|
| `question_type`   | Plain String  | false      | The type of the question. See the details for each question type below for the correct value of this field. |
| `prompt`          | Parsed String | false      | The prompt displayed for a question. All questions require a prompt. See [this additional description](/README.md#question-prompts). |
| `posints`         | Number        | true       | The max points available for the question. Defaults to 0. |
| `answers`         | -             | false      | The definition of the answer or possible answers for a question. Because of the diverse nature of questions, the answers value will look different for different question types. |
| `custom_header`   | Plain String  | true       | An alternate header for a question. An empty string for no header. |
| `skip_numbering`  | Boolean       | true       | Whether this question should skip incrementing the question number. |
| `shuffle_answers` | Boolean       | true       | Whether to shuffle the order of the choices for this question. The final value is the conjunction of values from the quiz, group, and question. |
| `hints`           | Object        | true       | Formatting hints passed the converter about this question. We will note any question type that specifically looks for hints. |

## Question Types

Below are details on all the QuizGen's supported question types.

### Multiple Choice (MC)

Question Type: `multiple_choice_question`

Multiple choice questions provide several different options (called distractors)
with a **single** correct option.
The QuizGen requires that there is exactly one correct choice,
but does not set any limit on the number of distractors (incorrect options).
Specific output formats may limit the maximum number of distractors.

Answers are formatted as an array of objects with the `correct` and `text` fields.
The value of the `correct` field must be a boolean indicating if this option is the correct answer.
The value of the `text` field is a Parsed String.

Example Answers Definition:
```json
    "answers": [
        {"correct": true,  "text": "A"},
        {"correct": false, "text": "B"},
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

### True-False (TF)

Question Type: `true_false_question`

True-False questions are like multiple choice questions that are limited to only two choices: "True" and "False".
The answers definition is just a single boolean indicating the correct answer.

Example Answers Definition:
```json
    "answers": true
```

### Multiple Drop-Downs (MDD)

Question Type: `multiple_dropdowns_question`

Multiple Drop-Down questions are questions that contain one or more parts,
where each part is a multiple choice question.
In a digital medium, each part could be represented with a drop-down selection list.
The question prompt should contain an [answer reference](/syntax.md#answer-references) for the location of each question part.
The answers definition then maps each answer reference to a multiple choice-style answers definition.

For example, a question may have the following prompt and answers definition:
```json
    "prompt": "[[part1]] and [[part2]] wait for no one.",
    "answers": {
        "part1": [
            {"correct": true,  "text": "Time"},
            {"correct": false, "text": "Busses"},
            {"correct": false, "text": "Cats"}
        ],
        "part2": [
            {"correct": true,  "text": "tides"},
            {"correct": false, "text": "death"},
            {"correct": false, "text": "dogs"}
        ]
    }
```

### Multiple Answers (MA)

Question Type: `multiple_answers_question`

Multiple answer questions are questions where multiple (or no) choices can be selected.
They are specified the same as multiple choice questions,
except any number of the choices may be marked as correct.

Output mediums will typically style these choices differently that multiple choice questions.
A common convention is to use round radio buttons when a single choice is available,
and square checkboxes when multiple choices are available.

Example Answers Definition:
```json
    "answers": [
        {"correct": true,  "text": "A"},
        {"correct": true,  "text": "B"},
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

### Matching

Question Type: `matching_question`

Matching questions provide two lists: left and right.
Users are tasked with matching an item from the left list to an item from the right list.
The right list will be at least as large as the left list,
and may contain additional distractors (incorrect values that do not match anything in the left list).

The answers definition must contain a list of pairs of left and right items,
and an optional list of additional distractors.
All values are parsed strings.

Example Answers Definition:
```json
    "prompt": "Match the English word to it's Spanish equivalent.",
    "answers": {
        "matches": [
            ["one", "uno"],
            ["two", "dos"],
            ["three", "tres"]
        ],
        "distractors": [
            "cuatro",
            "cuatro",
            "seis"
        ]
    }
```

### Fill in the Blank (FITB)

Question Type: `fill_in_the_blank_question`

Fill in the blank questions provide a single blank at the end of the question that the users is tasked with filling out.
These questions expect a finite textual answer.
Designing these questions can be tricky, since an exact answer is expected.
Stray spacing, capitalization, alternate spelling, phrasing, or bad handwriting can lead to incorrect automatic grading of these questions.
The semantics of how exactly answers are checked and case sensitivity is up to the output quiz medium (e.g. Canvas, GradeScope, etc).
It is recommended that you avoid FITB questions when possible.

Answers are defined as a list of possible correct answers.

Example Answers Definition:
```json
    "prompt": "How many cardinal directions are there?",
    "answers": ["4", "four", "Four", "FOUR"]
```

### Fill in Multiple Blanks (FIMB)

Question Type: `fill_in_multiple_blanks_question`

Fill in multiple blank questions are an extension of FITB questions that allows for multiple blanks to occur anywhere in the prompt.
Like MDD questions, the question prompt should include an answer reference for each blank.
FIMB questions come with the same warnings as FITB questions (multiplied by the number of blanks).

Answers map each blank to a list of possible options.

Example Answers Definition:
```json
    "prompt": "Nothing can be said to be certain, except [[first]] and [[second]].",
    "answers": {
        "first": ["death", "Death", "DEATH"],
        "second": ["taxes", "taxs", "Taxes", "Taxs," "TAXES", "TAXS"],
    }
```

#### Hints

FIMB questions may observe the "inline" hint.
This hint indicates that the output medium should attempt to reduce the reserved space for answers and place them on the same line
(if possible).

### Numeric

Question Type: `numerical_question`

Numeric questions are similar to FITB question,
but expect a single numerical answer.
Because a numerical answer is expected,
numeric questions are typically much less ambiguous than FITB questions.

The answers definition for numeric questions is a list of possible numeric ranges.
Matching any of these ranges indicates a correct answer.

Example Answers Definition:
```json
    "answers": [
        {"type": "exact", "value": 1.0, "margin": 0.01},
        {"type": "range", "min": 0.99, "max": 1.01},
        {"type": "precision", "value": 1.0, "precision": 2}
    ]
```

### Short Answer (SA)

Question Type: `short_answer_question`

Short answer questions provide a text area for users to enter answers.
Answers are expected to be anywhere between a few words to a few sentences.
There is no finite answer to short answer questions, they are intended to be manually graded.
As such, no `answers` key should be present in the question definition.

### Essay Questions

Question Type: `essay_question`

Essay questions are like short answer questions,
but allocate a much larger area for answers.
In a paper-based medium, an entire page should be reserved for an answer area.
Like SA questions, no `answers` key should be present in the question definition.

### Text-Only

Question Type: `text_only_question`

Text-only questions provide a means of communicating information to the user in a structured manner.
The most common use for text-only questions is to provide a common description or information that can be used
in multiple subsequent questions, e.g., a table that can be referenced across multiple questions.

## Differences with Canvas

The QuizGen supports almost all the questions used in "classic" style Canvas quizzes.

The only text-input Canvas question type the Quiz Generator does not support are "Calculated" / "Formula" questions.
We feel that this question type is overly complex and error-prone.
Instead, we suggest that users use the "numeric" question type.

Canvas users should also note that the "Fill in the Blank" (FITB) question type,
also referred to as "Short Answer" (SA) in Canvas documentation, has been split from one Canvas question type
into two QuizGen question types: "Fill in the Blank" (FITB) and "Short Answer" (SA).
When creating Canvas quizzes, both these types map back to the FITB type.
For other quiz mediums, FITB questions generally expect the answer to be no more than a few words and reserve only a little space for the answer,
while SA questions generally reserve about a paragraph's worth of space for an answer.