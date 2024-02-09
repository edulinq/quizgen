# Quiz Generator

A tool for generating quizzes from a standard, text-based definition.
Quizzes can be taken from the standard definition and converted into:
 - PDFs
 - Canvas Quizzes (Uploaded to Canvas)
 - GradeScope Quizzes
   - Both GradeScope-Compatible PDFs and Uploaded to GradeScope
 - HTML Forms

Sample quizzes that demonstrate all question types are available [in the CSE Cracks course](https://github.com/eriq-augustine/cse-cracks-course/tree/main/quizzes).
Additionally, you can see examples of good questions by looking at the [test cases for this project](tests/questions/good).

Documentation Table of Contents:
 - [Installation / Requirements](#installation--requirements)
   - [Python](#python)
   - [KaTeX (NodeJS)](#katex-nodejs)
   - [Canvas Uploading](#canvas-uploading)
   - [GradeScope Uploading](#gradescope-uploading)
 - [Usage](#usage)
   - [Parsing a Specific Quiz](#parsing-a-specific-quiz)
     - [Outputting a JSON Quiz](#outputting-a-json-quiz)
     - [Outputting a TeX Quiz](#outputting-a-tex-quiz)
     - [Outputting an HTML Quiz](#outputting-an-html-quiz)
   - [Parsing a Specific Question](#parsing-a-specific-question)
   - [Parsing a Specific File](#parsing-a-specific-file)
   - [Uploading a Quiz to Canvas](#uploading-a-quiz-to-canvas)
   - [Uploading a Quiz to GradeScope](#uploading-a-quiz-to-gradescope)
 - [Quiz Format](#quiz-format)
   - [Question Prompts](#question-prompts)
   - [Quiz Descriptions](#quiz-descriptions)
 - [Question Types](/question-types.md)
 - [QuizGen Markdown Syntax](/syntax.md)

## Installation / Requirements

### Python

The project can be installed from PyPi with:
```
pip install eq-quizgen
```

Standard Python requirements are listed in `pyproject.toml`.
The project and Python dependencies can be installed from source with:
```
pip3 install .
```

### KaTeX (NodeJS)

To output equations in HTML documents (which includes Canvas), [KaTeX](https://katex.org) is required.
KaTeX is distributed as a NodeJS package, and this project requires that KaTeX is accessible via `npx` (which typically requires it to be installed via `npm`).
Once NodeJS and NPM are installed, you can just install KaTeX normally:
```
npm install katex
```

### Canvas Uploading

To upload quizzes to Canvas, you will need three things:
 - The Canvas Base URL
   - The base URL for the Canvas instance you are using.
   - Ex: `https://canvas.ucsc.edu`
 - The Canvas Course ID
   - The numeric ID for the course you want to upload the quiz under.
   - You can find this by going to the main page for your course (or almost any page related to your course), and looking at the url.
   - Ex: For `https://canvas.ucsc.edu/courses/12345`, the course ID is `12345`.
 - A Canvas Access Token
   - A token is specific for each user, and that user should the have ability to make quizzes for your specific course.
   - To get a new token, go to your account settings ("Account" -> "Settings"), and under "Approved Integrations" click "+ New Access Token".

### GradeScope Uploading

To upload quizzes to GradeScope, you will need three things:
 - A GradeScope Instructor Account
   - Technically, any account capable of creating assignments should be sufficient.
 - A GradeScope Account Password
   - If you normally log into GradeScope through an organization account (like via a university email), then you will just need to create a GradeScope password.
     This can be done via the [password reset page](https://www.gradescope.com/reset_password), which in this case will allow you to create a new password.
 - A GradeScope Course ID

## Usage

This project has executable modules in the `quizgen.cli` package.
All executable modules have their own help/usage accessible with the `-h` / `--help` option.

### Parsing a Specific Quiz

To parse an entire specific quiz, you can use the `quizgen.cli.parse-quiz` module.
This is useful if you want to check if a quiz properly parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse.quiz <path to quiz JSON file>
```

This command will output the fully parsed quiz in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
Parsing a quiz is particularly useful in CI to ensure that all course quizzes are properly maintained.

The `--key` flag can be used to generate an answer key instead of a normal quiz.
Not all formats support answer keys.

#### Outputting a JSON Quiz

To output a JSON quiz to a file called `quiz.json`, you can use the following command:
```
python3 -m quizgen.cli.parse.quiz <path to quiz JSON file> --format json > quiz.json
```

A JSON representation of a parsed quiz (which is different from a standard quiz definition) can be useful for debugging.
If debugging, the `--flatten-groups` flag can be useful (which will include all questions from all groups in the output quiz.

#### Outputting a TeX Quiz

To output a TeX quiz to a file called `quiz.tex`, you can use the following command:
```
python3 -m quizgen.cli.parse.quiz <path to quiz JSON file> --format tex > quiz.tex
```

You can then compile or edit the TeX file as you see fit.

#### Outputting an HTML Quiz

To output a HTML quiz to a file called `quiz.html`, you can use the following command:
```
python3 -m quizgen.cli.parse.quiz <path to quiz JSON file> --format html > quiz.html
```

All question in an HTML quiz are grouped together into a single HTML form.

### Parsing a Specific Question

To parse a specific quiz question, you can use the `quizgen.cli.parse.question` module.
This is useful if you want to check if a question properly parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse.question <path to question JSON file>
```

This command will output the fully parsed question in the JSON format,
and will exit with a non-zero status if the parse failed.

You can use the same `--format` options used in `quizgen.cli.parse.quiz` to change the output format of the question.
The question will be placed in a "dummy" quiz, so the output should be fully stand-alone.

### Parsing a Specific File

To parse a specific file, you can use the `quizgen.cli.parse.file` module.
This is useful if you want to check if/how a specific document parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse.file <path to file> --format html
```

This command will output the fully parsed file in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
This can be used to parse prompt markdown files.

### Uploading a Quiz to Canvas

To upload a quiz to Canvas, the `quizgen.cli.canvas.upload` module can be used.
The basic usage is as follows:
```
python3 -m quizgen.cli.canvas.upload <path to quiz JSON file> --course <canvas course id> --token <canvas access token>
```

If an existing quiz with the same name is found, then nothing will be uploaded unless the `--force` flag is given..

### Uploading a Quiz to GradeScope

To upload a quiz to GradeScope, the `quizgen.cli.gradescope.create` module can be used.
The basic usage is as follows:
```
python3 -m quizgen.cli.gradescope.gradescope <path to quiz JSON file> --course <course id> --user <username> --pass <password> --upload
```

Since GradeScope uses passwords instead of tokens, take extra caution about your password appearing in config files or command histories.

Some additional options that may be useful:
 - `--force` -- Use if you want to replace existing GradeScope assignments (otherwise existing assignments will be skipped).
 - `--outdir <dir>` -- Choose where the output (TeX, PDF, etc) will be written to.
 - `--variants <X>` -- Create X variants (alternate versions) if the quiz. X may be in [1, 26].

You can also not use the `--upload` flag to just create TeX/PDF versions of your quizzes that you can tweak and upload manually.

## Quiz Format

### Question Prompts

Question prompts can be provided in two ways:
 - In a "prompt" field in the `question.json`.
 - In a file adjacent to the `question.json` file called `prompt.md`.

Putting the prompt directly in the JSON can be convenient for questions with short or simple prompts.
But for larger prompts that may involve things like tables and images,
having a whole file just for the prompt is generally recommended.

**WARNING**: Remember that in JSON backslashes will need to be escaped.
So prompts written in JSON will need to escape backslashes
(which then in-turn may be used to escape characters in QuizGen markdown).

For example, in markdown you may have a prompt like:
```
This is a cool\-ish question.
```

In JSON this would need to be:
```
"prompt": "This is a cool\\-ish question."
```

### Quiz Descriptions

Like question prompts, quiz descriptions can either be specified in the quiz's JSON file,
or in an adjacent file with the same base filename as the quiz's JSON file but with the `md` extension.

For example, the description could be in the `my_quiz.json` file:
```
"description": "Look at my awesome quiz\\!"
```

Or, it can be in the `my_quiz.md` file in the same directory as `my_quiz.json`:
```
Look at my awesome quiz\!
```
