import quizgen.constants
import quizgen.converter.htmltemplate
import quizgen.converter.json
import quizgen.converter.textemplate
import quizgen.variant

SUPPORTED_FORMATS = [
    quizgen.constants.DOC_FORMAT_HTML,
    quizgen.constants.DOC_FORMAT_JSON,
    quizgen.constants.DOC_FORMAT_TEX,
]

def get_converter_class(format = quizgen.constants.DOC_FORMAT_JSON):
    if (format == quizgen.constants.DOC_FORMAT_JSON):
        return quizgen.converter.json.JSONConverter
    elif (format == quizgen.constants.DOC_FORMAT_HTML):
        return quizgen.converter.htmltemplate.HTMLTemplateConverter
    elif (format == quizgen.constants.DOC_FORMAT_TEX):
        return quizgen.converter.textemplate.TexTemplateConverter
    else:
        raise ValueError("No known converter for format '%s'." % (format))

def get_converter(format = quizgen.constants.DOC_FORMAT_JSON, **kwargs):
    converter_class = get_converter_class(format = format)
    return converter_class(**kwargs)

def convert_variant(variant, format = quizgen.constants.DOC_FORMAT_JSON,
        constructor_args = {}, converter_args = {}):
    if (not isinstance(variant, quizgen.variant.Variant)):
        raise ValueError("convert_variant() requires a quizgen.variant.Variant type, found %s." % (type(variant)))

    converter = get_converter(format = format, **constructor_args)
    return converter.convert_variant(variant, **converter_args)

def convert_question(question, format = quizgen.constants.DOC_FORMAT_JSON,
        constructor_args = {}, converter_args = {}):
    converter = get_converter(format = format, **constructor_args)
    return converter.convert_question(question, **converter_args)
