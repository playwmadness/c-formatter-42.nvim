import sys
from io import StringIO
from typing import cast

import pynvim
from norminette.context import Context
from norminette.exceptions import CParsingError
from norminette.file import File
from norminette.lexer import Lexer
from norminette.registry import Registry

failed_import = False

try:
    from c_formatter_42.run import run_all
except ImportError:
    failed_import = True
    print(
        "c_formatter_42 is not installed in your g:python3_host_prog", file=sys.stderr
    )

if failed_import:
    print(
        "Make sure all required dependencies are installed and try again",
        file=sys.stderr,
    )
    sys.exit(1)


@pynvim.plugin
class CFormatNvim:
    def __init__(self, nvim: pynvim.Nvim):
        self.nvim = nvim

    @pynvim.command(
        "CFormatNormSync",
        range="%",
        sync=True,
    )
    def format_sync(self, range):
        return self.format(range)

    @pynvim.command(
        "CFormatNorm",
        range="%",
    )
    def format(self, range):
        if self.nvim.current.buffer.options.get("filetype") != "c":
            self.nvim.err_write("Buffer filetype is not C\n")
            return

        buf = "\n".join(self.nvim.current.buffer[range[0] - 1 : range[1]])

        buf = run_all(buf)  # pyright: ignore

        cursor = self.nvim.current.window.cursor
        self.nvim.current.buffer[range[0] - 1 : range[1]] = buf.split("\n")[:-1]
        try:
            self.nvim.current.window.cursor = cursor
        except pynvim.NvimError:
            self.nvim.current.window.cursor = (len(self.nvim.current.buffer), 0)

    @pynvim.command(
        "Norminette",
        range="%",
        sync=True,
    )
    def norminette(self, range):
        if self.nvim.current.buffer.options.get("filetype") != "c":
            self.nvim.err_write("Buffer filetype is not C\n")
            return

        filepath: str = cast(str, self.nvim.current.buffer.options.get("name"))
        buf: str = "\n".join(self.nvim.current.buffer[range[0] - 1 : range[1]])

        file = File(filepath, buf)
        try:
            tokens = list(Lexer(file))
            context = Context(file, tokens)
            Registry().run(context)
        except CParsingError as e:
            self.nvim.err_write(e.msg)
            return
        except KeyboardInterrupt:
            return

        for err in file.errors:
            for highlight in err.highlights:
                self.nvim.current.window.cursor = (highlight.lineno, highlight.column)
                return
