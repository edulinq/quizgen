# Quiz Generator

A tool for generating quizzes from a standard definition into either Canvas quizzes or LaTeX pdf files.

NodeJS and the `katex` package is required for producing HTML equations.

## Syntax

The syntax for text fields is similar to [Markdown](https://www.markdownguide.org/basic-syntax/).

TODO

### Inline Text

TODO

#### Escape Characters

The following characters need to be escaped with a backslash when they appear in inline text:
 - `\`
 - `-`
 - `*`
 - `|`
 - `$`
 - `[`
 - `!`
 - `\``

#### Links

TODO

#### Inline Code

TODO

#### Inline Equations

TODO

### Code Blocks

TODO

### Tables

TODO

Tables need to have two newlines after them.
Should still parse, but there will not be the expected space between the table and next block/paragraph.

### Quirks

Markdown is an [inherintly ambiguous language](https://roopc.net/posts/2014/markdown-cfg/).
So, converting it into a language that can be represented by a CFG will mean a few quirks
(also, I am no programming languages expert).
Below are some quirks that should be noted.

TODO

Tables need to have two newlines after them.

Table seps must be between two rows (normal or header doesn't matter).
