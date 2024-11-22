import markdown_it.renderer
import mdformat.renderer

# TEST - Cache renderers

def html(tokens, options = {}, env = {}):
    renderer = markdown_it.renderer.RendererHTML()
    return renderer.render(tokens, options, env)

def markdown(tokens, options = {}, env = {}):
    renderer = mdformat.renderer.MDRenderer()
    return renderer.render(tokens, options, env)
