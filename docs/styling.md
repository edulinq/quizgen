# Styling

Styling can be used in the QuizGen to change the visual appearance of content.
If you want to change the location or flow of information,
then you are looking for [template hints](docs/builtin-templates.md).

Styling in the Quiz Generator is done via *style blocks* where specific options can be set.
Style blocks are surrounded by double braces (`{{` and `}}`).
Internally, style blocks use JSON object syntax.
For example:

```
{{
    "font-size": 12
}}
```

Most styling needs can be answered by the [FAQ](#faq) or by looking over the [styling options](#style-options),
for more advanced use cases see the [Blocks & Style Blocks](#blocks--style-blocks) section.

Table of Contents:
 - [FAQ](#faq)
   - [How do I center something?](#faq-center)
   - [How do I resize an image?](#faq-resize-image)
 - [Style Options](#style-options)
   - [Alignment](#alignment)
   - [Font Size](#font-size)
   - [Image Width](#image-width)
 - [Blocks & Style Blocks](#blocks--style-blocks)
   - [Overriding Style](#overriding-style)
   - [Clearing Style](#clearing-style)

## FAQ

TEST
FAQ first, since most people will just need this little bit of information.

<a name="faq-align"></a>
### How do I (left, center, right) align something?

You can center something (image, table, text, etc) using the [alignment](#alignment) style options.
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
Only the width of an image can be explicitly set.
The aspect ratio of the image will be preserved, which will determine the height of the image.

For example, to make an image 50% it's normal size:
```
{{
    "image-width": 0.5
}}

![Great Dane](../tests/data/great-dane.jpg)
```

See the [`image-width` documentation](#image-width) for more information.

## Style Options

### Alignment

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
Content alignment will also affect text and text alignment will not work within normal paragraphs.

#### Content Align

| Key           | `content-size`              |
| Type          | string                      |
| Range         | {`left`, `center`, `right`} |
| Default Value | null                        |

#### Text Align

| Key           | `text-size`                 |
| Type          | string                      |
| Range         | {`left`, `center`, `right`} |
| Default Value | null                        |

### Font Size

| Key           | `font-size`     |
| Type          | float           |
| Range         | (0.0, infinity] |
| Default Value | null            |

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

| Key           | `image-width` |
| Type          | float         |
| Range         | (0.0, 1.0]    |
| Default Value | 1.0           |

`image-width` can be used to set the width of an image.
The width is given as **a ratio** of the image's parent container's width.
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
