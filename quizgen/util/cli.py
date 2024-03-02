import os

def add_out_arg(parser, default_filename,
        name = 'out', dest = 'out', default = '.'):
    """
    Add a standard output path argument to an argparse parser.
    """

    parser.add_argument(f'--{name}', dest = dest,
        action = 'store', type = str, default = default,
        help = ('The path specifying where to put the output.'
                + f' If the path points to an existing dir, the result will be written to `<{name}>/{default_filename}`.'
                + ' If the path point to an existing file, the file will be overwritten with the result.'
                + ' If the path points to a non-existing dir (denoted with a trailing path separator (e.g., slash)), the dir will be created and the output will be written as it is to an existing dir.'
                + ' Finally if the path does not exist, the result will be written to the full path (creating any parent directories along the way).'
                + ' (default: %(default)s).'))

def resolve_out_arg(raw_path, default_filename):
    """
    Resolve the out argument with the semantics of add_out_arg(),
    and return a resolved normalized path.
    """

    path = os.path.abspath(raw_path)

    if (os.path.isfile(path)):
        return path
    elif (os.path.isdir(path)):
        return os.path.join(path, default_filename)
    elif (raw_path.endswith(os.sep)):
        os.makedirs(path, exist_ok = True)
        return os.path.join(path, default_filename)
    else:
        os.makedirs(os.path.dirname(path), exist_ok = True)
        return path
