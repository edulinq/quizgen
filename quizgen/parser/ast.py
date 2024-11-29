import markdown_it

import quizgen.parser.common

# Pull these attributes out of these specific token types when building the AST.
AST_TOKEN_ATTRS = {
    'image': [
        'src',
    ],
    'link': [
        'href',
    ],
    'td': [
        'style',
    ],
    'th': [
        'style',
    ],
}

# Grab the 'tags' field for these node types.
AST_NODE_TAG_TYPES = {
    'heading',
}

# Like AST_TOKEN_ATTRS, but for the `meta` property.
AST_TOKEN_METAS = {
    'container_block': [
        quizgen.parser.common.TOKEN_META_KEY_ROOT,
        quizgen.parser.common.TOKEN_META_KEY_STYLE,
    ]
}

class ASTNode(dict):
    def type(self):
        return self['type']

    def children(self):
        return self.get('children', [])

    def text(self):
        return self.get('text', '')

def build(tokens):
    tree = markdown_it.tree.SyntaxTreeNode(tokens)
    return _walk_ast(tree)

def _walk_ast(node):
    result = {
        'type': node.type,
    }

    if (node.type in quizgen.parser.common.CONTENT_NODES):
        result['text'] = node.content

    if (node.type in AST_NODE_TAG_TYPES):
        result['tag'] = node.tag

    for name in AST_TOKEN_ATTRS.get(node.type, []):
        value = node.attrGet(name)
        if (value is not None):
            result[name] = value

    for name in AST_TOKEN_METAS.get(node.type, []):
        value = node.meta.get(name, None)
        if (value is not None):
            result[name] = value

    if (len(node.children) > 0):
        result['children'] = [_walk_ast(child) for child in node.children]

    return ASTNode(result)
