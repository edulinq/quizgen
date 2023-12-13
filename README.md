# Quiz Generator

A tool for generating quizzes from a standard definition into either Canvas quizzes (which will be automatically uploaded) or TeX files.

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

Additionally, to output equations in HTML documents, [KaTeX](https://katex.org) is required.
KaTeX is distributed as a NodeJS package, and this project requires that is is accessible via `npx` (which typically requires it to be installed via `npm`).
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

## Usage

This project has executable modules in the `quizgen.cli` package.
All executable modules have their own help/usage accessible with the `-h` / `--help` option.

### Uploading a Quiz to Canvas

To upload a quiz to Canvas, the `quizgen.cli.upload-quiz` module can be used.
The basic usage is as follows:
```
python3 -m quizgen.cli.upload-quiz <path to quiz json file> --course <canvas course id> --token <canvas access token>
```

Where the format (shown as `html`) can be one of: `json`, `html`, `md`, and `tex`.

### Parsing a Specific Quiz

To parse an entire specific quiz, you can use the `quizgen.cli.parse-quiz` module.
This is useful if you want to check if a quiz properly parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse-quiz <path to quiz file>
```

### Parsing a Specific File

To parse a specific file, you can use the `quizgen.cli.parse-file` module.
This is useful if you want to check if/how a specific document parses.
The basic usage is as follows:
```
python3 -m quizgen.cli.parse-file <path to file> --format html
```

Where the format (shown as `html`) can be one of: `json`, `html`, `md`, and `tex`.

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

Equation blocks are similar to code blocks, but with three dollar sign characters `$$$`.
Like code blocks, the dollar signs should generally be one their own line.

```
The below equation is in its own block.

$$$
    \text{some_func}(a, b) = a + b
$$$

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
