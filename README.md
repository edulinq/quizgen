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
python3 -m quizgen.cli.parse-quiz <path to quiz JSON file>
```

This command will output the fully parsed quiz in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
Parsing a quiz is particularly useful in CI to ensure that all course quizzes are properly maintained.

The `--key` flag can be used to generate an answer key instead of a normal quiz.
Not all formats support answer keys.

#### Outputting a JSON Quiz

To output a JSON quiz to a file called `quiz.json`, you can use the following command:
```
python3 -m quizgen.cli.parse-quiz <path to quiz JSON file> --format json > quiz.json
```

A JSON representation of a parsed quiz (which is different from a standard quiz definition) can be useful for debugging.
If debugging, the `--flatten-groups` flag can be useful (which will include all questions from all groups in the output quiz.

#### Outputting a TeX Quiz

To output a TeX quiz to a file called `quiz.tex`, you can use the following command:
```
python3 -m quizgen.cli.parse-quiz <path to quiz JSON file> --format tex > quiz.tex
```

You can then compile or edit the TeX file as you see fit.

To generate TeX that is GradeScope-compatible, use the `gradescope` format instead:
```
python3 -m quizgen.cli.parse-quiz <path to quiz JSON file> --format gradescope > quiz.tex
```

#### Outputting an HTML Quiz

To output a HTML quiz to a file called `quiz.html`, you can use the following command:
```
python3 -m quizgen.cli.parse-quiz <path to quiz JSON file> --format html > quiz.html
```

HTML quizzes are grouped together into a single form.

### Parsing a Specific Question

To parse a specific quiz question, you can use the `quizgen.cli.parse-question` module.
This is useful if you want to check if a question properly parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse-question <path to question JSON file>
```

This command will output the fully parsed question in the JSON format,
and will exit with a non-zero status if the parse failed.

### Parsing a Specific File

To parse a specific file, you can use the `quizgen.cli.parse-file` module.
This is useful if you want to check if/how a specific document parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse-file <path to file> --format html
```

This command will output the fully parsed file in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
This can be used to parse prompt markdown files.

### Uploading a Quiz to Canvas

To upload a quiz to Canvas, the `quizgen.cli.upload-canvas-quiz` module can be used.
The basic usage is as follows:
```
python3 -m quizgen.cli.upload-canvas-quiz <path to quiz JSON file> --course <canvas course id> --token <canvas access token>
```

If an existing quiz with the same name is found, then nothing will be uploaded unless the `--force` flag is given..

### Uploading a Quiz to GradeScope

To upload a quiz to GradeScope, the `quizgen.cli.create-gradescope-quiz` module can be used.
The basic usage is as follows:
```
python3 -m quizgen.cli.create-gradescope-quiz <path to quiz JSON file> --course <course id> --user <username> --pass <password> --upload
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

## Syntax

The syntax for text fields is similar to [Markdown](https://www.markdownguide.org/basic-syntax/).
This should generally make files readable as both text files and by Markdown readers (e.g. via GitHub's web GUI).

Documents are separated into "blocks" which are generally separated by a blank line (which literally translates to two newline characters).
This can be a little tricky with some structures like tables (which use newline characters as a row delimiter),
so if you want to be safe you can separate blocks with two empty lines.

In general, when text structure (code, table, links, etc) require some sort of context to be in them.
So empty code blocks may throw an error.

### Text

Text is generally written the same way as markdown.

#### Escape Characters

The following characters need to be escaped with a backslash when they appear in inline text:
 - `/` - Slash / Forward Slash
 - `\` - Backslash
 - `-` - Dash
 - `*` - Star / Asterisk
 - `|` - Pipe
 - `$` - Dollar Sign
 - `[` - Open Bracket
 - `!` - Bang / Exclamation Point
 - `` ` `` - Backtick

These characters do not need to be escaped inside code, equations, and comments.

#### Comments

Line comments that start with two slashes (`//`) are supported.
Block comments are not supported.

```
// This shows a full line comment.

Some text // Here is a comment after text.

// `code that is commented out`
```

Note that the more standard markdown comments (HTML comments) are not supported.
This is because we want comments to show up in the rendered markdown.

#### Text Style

The markdown syntax for italics and bold is supported.

```
Some *italics* text.
Some **bold** text.
```

#### Line Break

Blocks will always be separated by some whitespace.
To add in a line break within a block, the characters `\n` can be used.
(Note that this is not a literal newline/linefeed character, but a backslash followed by the letter "n".

#### Links

Links are done the same as in markdown: `[text](url)`.

```
// A normal link.
[Normal Link](https://linqs.org)

// A link with no text (the url will be used as the text).
[ ](https://some.link/with/no.text
```

#### Inline Code

Inline code is done the same as Markdown, where the code is surrounded with a single backtick character `` ` ``.

```
Some text with `code()` inside it.
```

### Code Blocks

Code blocks done the same as markdown, with three backticks `` ``` ``.
The three backticks should generally be on their own line.

````
The below code is in its own block.

```
def some_func(a, b):
    return a + b
```

Where `a` and `b` should be positive.
````

#### Inline Equations

Inline equations are done the same as Markdown, where the equation is surrounded with a single dollar sign character `$`.

```
Let $ f $ be defined as $ f(x) = x^2 + \aplha $ where $ \alpha > 3 $.
```

Most standard LaTeX math syntax and operators are supported.
When converting a document to LaTeX, the contents of an equation will just be dumped into a math context verbatim.
When converting a document to HTML, KaTeX will be used to convert the equation to HTML.

### Equation Blocks

Equation blocks are similar to code blocks, but with two dollar sign characters `$$`.
Like code blocks, the dollar signs should generally be one their own line.

```
The below equation is in its own block.

$$
    \text{some_func}(a, b) = a + b
$$

Where $ a $ and $ b $ should be positive.
```

### Tables

Basic tables are supported.
Vanilla markdown does not support tables, and there are several extended markdown languages that support tables.
Our syntax is similar to Github-Flavored Markdown (GFM), but does not support more advanced features.

Tables should be in their own block,
and are composed of multiple table rows.
A table row can be either a normal row, a header row, or a separator row.
Each type of row must start on a new line with a pipe character `|`.

A normal table row has a space after the initial pipe, followed by at least one table cell.
A table tell is standard inline text (which can include things like inline code, inline equations, etc)
followed by a pipe character.
The contents of table cells will be stripped of leading and trailing whitespace.

A header row is like a normal row, but has a dash directly following the initial pipe character.
Header rows will be rendered with different styling from normal rows.

A separator row starts with a pipe and at least three dashes followed by another pipe.
Everything else on the line is ignored.
A table separator cannot be the first or last row of a table.
Although not required, it is common markdown style to pad separators so they match the rest of the table.
Separator rows will be rendered as a horizontal rule in the table.

```
|- Some | Header | Row |
|-------|--------|-----|
| 1     | \-2    | N/A |
| *a*   | **b**  | $x$ |
```

### Lists

Basic lists are supported.
Lists should be in their own block
and are a series of list items.
List items begin with a dash `-` character and may be preceded by any amount of whitespace.
The text of each list item will be stripped of leading and trailing whitespace.

Nested lists are not supported.

```
 - Item 1.
 - Item $ 2 $.
 - A `third()` item.
```

### Answer References

Answer references are used in questions that can have multiple parts (like multiple drop-downs).
To make an answer reference, just surround a key in double square brackets.
For example:

```
[[key]]
[[answer_reference]]
[[part1]]
[[a]]
[[A]]
```

Because of Canvas limitations, the key for an answer reference must match the following regular expression:
`^[a-zA-Z][a-zA-Z0-9_]*$`

### Quirks

Markdown is an [inherently ambiguous language](https://roopc.net/posts/2014/markdown-cfg/),
so converting it into a language that can be represented by a CFG will mean a few quirks.
Below are some quirks that should be noted:

 - Tables and lists need to have two blank lines after them (hence the general recommendation that all blocks be separated by two blank lines).
 - Table separators cannot be the first or last row.
 - Table cells, list items, and equations will be stripped of leading and trailing whitespace.
 - Most syntax that surrounds some text requires that there be something inside (e.g. you cannot have an empty inline code).
 - Leading and trailing new lines in code blocks will be stripped.
 - Bold and italics cannot be nested.
