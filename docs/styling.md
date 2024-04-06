# Styling

Styling can be used in the QuizGen to change the visual appearance of content.
If you want to change the location or flow of information,
then you are looking for [template hints](docs/builtin-templates.md).

Styling in the Quiz Generator is done via *style blocks* where specific options can be set.
Style blocks are surrounded by double braces (`{{` and `}}`).
Internally, style blocks use JSON object syntax.
For example, the following style block will set the font size.

```
{{
    "font-size": 12
}}
```

By default, a style block will apply to all content in the document,
even if that content appears before or after the style block.
To set styling information for a subset of your document,
see the [Blocks & Style Blocks](#blocks--style-blocks) section.

The styling functionality provided is intended to be simple and cover some common use cases.
If you have styling needs that are not covered here,
then you can achieve you desired style by editing the output of the QuizGen or by using a custom template.

Table of Contents:
 - [FAQ](#faq)
   - [How do I left/center/right align something](#faq-align)
   - [How do I resize an image?](#faq-resize-image)
 - [Style Options](#style-options)
   - [Alignment](#alignment)
   - [Font Size](#font-size)
   - [Image Width](#image-width)
   - [Tables](#tables)
     - [Cell Size](#cell-size)
     - [Table Borders](#table-borders)
 - [Blocks & Style Blocks](#blocks--style-blocks)
   - [Overriding Style](#overriding-style)
   - [Clearing Style](#clearing-style)

## FAQ

The FAQ should be the first place to check for styling questions.

<a name="faq-align"></a>
### How do I left/center/right align something?

You can align something (image, table, text, etc) using the [alignment](#alignment) style options.
For non-text things (images, tables, containers, etc) you can use the `content-align` option,
and for text alignment, you can use the `text-align` option.

Both options support the following values: {`left`, `center`, `right`}.

For example, to center an image:
```
{{
    "content-align": "center"
}}

![Great Dane](../tests/data/great-dane.jpg)
```

To center align a table, but right align the text inside the table, you can do:
```
{{
    "content-align": "center",
    "text-align": "right"
}}

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

See the [alignment documentation](#alignment) for more information.

<a name="faq-resize-image"></a>
### How do I resize an image?

The size of an image can be controlled using the `image-width` value.
Only the width of an image can be explicitly set,
and the aspect ratio of the image will be preserved.

For example, to make an image 50% it's normal size:
```
{{
    "image-width": 0.5
}}

![Great Dane](../tests/data/great-dane.jpg)
```

Image width is provided as a proportion of the image container's width.

See the [`image-width` documentation](#image-width) for more information.

## Style Options

This section cover all the known style options
and details on their semantics.
For all options, `null` is always an allowed value,
and indicates that the default behavior should be used.

### Alignment

| Key             | Type   | Default Value | Allowed Values              | Notes |
|-----------------|--------|---------------|-----------------------------|-------|
| `content-align` | string | `null`        | {`left`, `center`, `right`} | By default, alignment is dependent on the output format. |
| `text-align`    | string | `null`        | {`left`, `center`, `right`} | By default, alignment is dependent on the output format. |

Alignment determines where on the horizontal axis content will appear:
`left`, `center`, or `right`.
Objects are split into two groups for the purposes of alignment:
non-text (content) and text.
Non-text (content) objects (images, tables, containers, etc) are aligned using the `content-align` key,
while text is aligned using the `text-align` key.

When not specified, the output format/converter determines alignment.

For example, to center align a table but right align the text inside the table:
```
{{
    "content-align": "center",
    "text-align": "right"
}}

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

*Warning*: Alignment does not work well within TeX documents.
In TeX, content alignment will also affect text and text alignment will not work within normal paragraphs.

### Font Size

| Key         | Type  | Default Value | Allowed Values  | Notes |
|-------------|-------|---------------|-----------------|-------|
| `font-size` | float | `null`        | (0.0, infinity] | Size in points. |

`font-size` can be used to set the font size **in points** ([typographic points](https://en.wikipedia.org/wiki/Point_(typography)).
Fractional point sizes (e.g. 12.5) are allowed,
but the exact support depends on the output format.

For example, a 12 point font can be set with:
```
{{
    "font-size": 12
}}
```

### Image Width

| Key           | Type  | Default Value | Allowed Values  | Notes |
|---------------|-------|---------------|-----------------|-------|
| `image-width` | float | 1.0           | (0.0, 1.0]      | Width relative to container. |

`image-width` can be used to set the width of an image.
The width is given as **a proportion** of the image's parent container's width.
This will typically mean the width of the page.
So `0.5` will set the image size to half of it's container.
Values above 1.0 are allowed, but the behavior is undefined.

Examples:

Use the full width:
```
{{
    "image-width": 1.0
}}
```

Use half the available width:
```
{{
    "image-width": 0.5
}}
```

### Tables

| Key                  | Type    | Default Value | Allowed Values    | Notes |
|----------------------|---------|---------------|-------------------|-------|
| `table-head-bold`    | boolean | `true`        | {`true`, `false`} | Bold table headers. |
| `table-cell-height`  | float   | `1.5`         | [1.0, infinity]   | In [em](https://en.wikipedia.org/wiki/Em_(typography)). Set the vertical size in a cell. |
| `table-cell-width`   | float   | `1.5`         | [1.0, infinity]   | In [em](https://en.wikipedia.org/wiki/Em_(typography)). Set the horizontal size in a cell. |
| `table-border-table` | boolean | `false`       | {`true`, `false`} | Sets the border *around* the table. |
| `table-border-cells` | boolean | `false`       | {`true`, `false`} | Sets the border *inside* the table (around each cell). |

Some basic options to control the look of tables are provided.

#### Cell Size

The size of cells can be set using the `table-cell-height` and `table-cell-width` options.
These options take a value no smaller than 1.0 in [em units](https://en.wikipedia.org/wiki/Em_(typography)).
Note that exact table size computations depend on the output format
and typically are the maximum of all the cells in a column/row.

To make a very tight table, you can use 1.0:
```
{{
    "table-cell-height": 1.0,
    "table-cell-width": 1.0
}}
```

To make a very spacious table, you can use something larger (like 2.0):
```
{{
    "table-cell-height": 2.0,
    "table-cell-width": 2.0
}}
```

#### Table Borders

There are two options that control border for tables:
`table-border-table` and `table-border-cells`.
Both are off (`false`) by default.
`table-border-table` controls borders *around* the table itself,
while `table-border-cells` controls the borders *inside* the table (and around each cell).
Note that any cell border that overlaps with the border of the actual table
(e.g., the top border of the first row) is controlled by `table-border-table` and **not** `table-border-cells`.

To get a table with full borders, use:
```
{{
    "table-border-table": true,
    "table-border-cells": true
}}
```

To get a table that only has dividers/borders between cells and not around the table itself, use:
```
{{
    "table-border-table": false,
    "table-border-cells": true
}}
```

## Blocks & Style Blocks

A styling rule applies within the *block* it was declared in,
and all children of that block.
By default, any QuizGen document starts out in a default block (called the "root" block).

Further blocks can be explicitly defined by surrounding content with the `{-` and `-}` symbols.
These symbols should appear on their own lines.

For example, here we have the root block with a single child block:
```
Root Block

{-

Child Block

-}

Still Root Block
```

A styling option set in the root block will apply to all children (and descendants).
```
{{
    "font-size": 13
}}

Root Block, will use 13pt font.

{-

Child Block, will also use 13pt font.

-}
```

However, style defined in a child block will not apply to any parents, ancestors, or siblings.
```
Root Block, will use the default font size.

{-

{{
    "font-size": 13
}}


Child Block, will use 13pt font.

-}
```

### Overriding Style

If the same styling rule is defined in a child block,
the value defined in the child will override the parent's value.

```
{{
    "font-size": 13
}}

Root Block, will use 13pt font.

{-

{{
    "font-size": 24
}}


Child Block, will use 24pt font.

-}
```

### Clearing Style

To clear an option set by a parent block
(and therefore use the default style),
an option can be set to the `null` value.

```
{{
    "font-size": 13
}}

Root Block, will use 13pt font.

{-

{{
    "font-size": null
}}


Child Block, will use the default font size.

-}
