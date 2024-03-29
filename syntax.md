# QuizGen Markdown Syntax

The Quiz Generator uses a syntax for text fields that is similar to [Markdown](https://www.markdownguide.org/basic-syntax/).
This should generally make files readable as both text files and by Markdown readers (e.g. via GitHub's web GUI).

Documents are separated into "blocks" which are generally separated by a blank line (which literally translates to two newline characters).
This can be a little tricky with some structures like tables (which use newline characters as a row delimiter),
so if you want to be safe you can separate blocks with two empty lines.

In general, when text structure (code, table, links, etc) require some sort of context to be in them.
So empty code blocks may throw an error.

Table of Contents:
 - [Text](#text)
   - [Escape Characters](#escape-characters)
   - [Comments](#comments)
   - [Text Style](#text-style)
   - [Line Break](#line-break)
   - [Links](#links)
   - [Images](#images)
   - [Inline Code](#inline-code)
 - [Code Blocks](#code-blocks)
   - [Inline Equations](#inline-equations)
 - [Equation Blocks](#equation-blocks)
 - [Tables](#tables)
 - [Lists](#lists)
 - [Answer References](#answer-references)
 - [Quirks](#quirks)

## Text

Text is generally written the same way as markdown.

### Escape Characters

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

### Comments

Line comments that start with two slashes (`//`) are supported.
Block comments are not supported.

```
// This shows a full line comment.

Some text // Here is a comment after text.

// `code that is commented out`
```

Note that the more standard markdown comments (HTML comments) are not supported.
This is because we want comments to show up in the rendered markdown.

### Text Style

The markdown syntax for italics and bold is supported.

```
Some *italics* text.
Some **bold** text.
```

### Line Break

Blocks will always be separated by some whitespace.
To add in a line break within a block, the characters `\n` can be used.
(Note that this is not a literal newline/linefeed character, but a backslash followed by the letter "n".

### Links

Links are done the same as in markdown: `[text](url)`.

```
// A normal link.
[Normal Link](https://linqs.org)

// A link with no text (the url will be used as the text).
[ ](https://some.link/with/no.text
```

## Images

Images can be include using the standard markdown syntax: `![alt text](url/path)`.

```
// An image with normal link.
![Banana Slugs](https://upload.wikimedia.org/wikipedia/commons/4/46/Two_Banana_Slugs.jpg)

// An image using a path.
![Great Dane](tests/data/great-dane.jpg)
```

All images pointing to a URL should start with "http/https".

Images will generally be placed in-line,
but can be put in their own block or even inside a table.

### Inline Code

Inline code is done the same as Markdown, where the code is surrounded with a single backtick character `` ` ``.

```
Some text with `code()` inside it.
```

## Code Blocks

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

### Inline Equations

Inline equations are done the same as Markdown, where the equation is surrounded with a single dollar sign character `$`.

```
Let $ f $ be defined as $ f(x) = x^2 + \aplha $ where $ \alpha > 3 $.
```

Most standard LaTeX math syntax and operators are supported.
When converting a document to LaTeX, the contents of an equation will just be dumped into a math context verbatim.
When converting a document to HTML, KaTeX will be used to convert the equation to HTML.

## Equation Blocks

Equation blocks are similar to code blocks, but with two dollar sign characters `$$`.
Like code blocks, the dollar signs should generally be one their own line.

```
The below equation is in its own block.

$$
    \text{some_func}(a, b) = a + b
$$

Where $ a $ and $ b $ should be positive.
```

## Tables

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

## Lists

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

## Answer References

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

## Quirks

Markdown is an [inherently ambiguous language](https://roopc.net/posts/2014/markdown-cfg/),
so converting it into a language that can be represented by a CFG will mean a few quirks.
Below are some quirks that should be noted:

 - Tables and lists need to have two blank lines after them (hence the general recommendation that all blocks be separated by two blank lines).
 - Table separators cannot be the first or last row.
 - Table cells, list items, and equations will be stripped of leading and trailing whitespace.
 - Most syntax that surrounds some text requires that there be something inside (e.g. you cannot have an empty inline code).
 - Leading and trailing new lines in code blocks will be stripped.
 - Bold and italics cannot be nested.
