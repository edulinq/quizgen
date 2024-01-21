# Quiz Generator Question Types

The Quiz Generator (QuizGen) supports several different types of questions

# TODO: TOC

## Differences with Canvas

The QuizGen supports almost all the questions used in "classic" style Canvas quizzes.

The only text-input Canvas question type the Quiz Generator does not support are "Calculated" / "Formula" questions.
We feel that this question type of overly complex and error-prone.
Instead, we suggest that users use the "numeric" question type.

Canvas users should also note that the "Fill in the Blank" (FITB) question type,
also referred to as "Short Answer" (SA) in Canvas documentation, has been split from one Canvas question type
into two QuizGen question types: "Fill in the Blank" (FITB) and "Short Answer" (SA).
When creating Canvas quizzes, both these types map back to the FITB type.
For other quiz mediums, FITB questions generally expect the answer to be no more than a few words and reserve only a little space for the answer,
while SA questions generally reserve about a paragraph's worth of space for an answer.

## Question Types

Below are details on all the QuizGen's supported question types.

### Multiple Choice (MC)

Identifier: `multiple_choice_question`

TODO

### True-False (TF)

Identifier: `true_false_question`

TODO

### Multiple Drop-Downs (MCC)

Identifier: `multiple_dropdowns_question`

TODO

### Multiple Answers (MA)

Identifier: `multiple_answers_question`

TODO

### Matching

Identifier: `matching_question`

TODO

### Fill in the Blank (FITB)

Identifier: `fill_in_the_blank_question`

TODO

### Fill in Multiple Blanks (FIMB)

Identifier: `fill_in_multiple_blanks_question`

TODO

### Short Answer (SA)

Identifier: `short_answer_question`

TODO

### Numeric

Identifier: `numerical_question`

TODO

### Essay Questions

Identifier: `essay_question`

TODO

### Text-Only

Identifier: `text_only_question`

TODO
