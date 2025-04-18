import sys
from typing import cast

import pynvim

failed_import = False

try:
    from c_formatter_42.run import run_all
except ImportError:
    failed_import = True
    print(
        "c_formatter_42 is not installed in your g:python3_host_prog", file=sys.stderr
    )

try:
    from norminette.context import Context
    from norminette.exceptions import CParsingError
    from norminette.file import File
    from norminette.lexer import Lexer
    from norminette.registry import Registry
except ImportError:
    failed_import = True
    print("norminette is not installed in your g:python3_host_prog", file=sys.stderr)

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
        self.namespace = nvim.api.create_namespace("c-formatter-42")

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
        if self.nvim.current.buffer.options.get("filetype") not in ["c", "cpp"]:
            self.nvim.err_write("Buffer filetype is not C\n")
            return

        buf = "\n".join(self.nvim.current.buffer[range[0] - 1 : range[1]])

        buf = run_all(buf)

        cursor = self.nvim.current.window.cursor
        self.nvim.current.buffer[range[0] - 1 : range[1]] = buf.split("\n")
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
        if self.nvim.current.buffer.options.get("filetype") not in ["c", "cpp"]:
            self.nvim.err_write("Buffer filetype is not C\n")
            return

        filepath: str = cast(str, self.nvim.current.buffer.name or "")
        buf: str = "\n".join(self.nvim.current.buffer[range[0] - 1 : range[1]]) + "\n"

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

        cursor_set = False

        self.nvim.api.buf_clear_namespace(
            self.nvim.current.buffer, self.namespace, 0, -1
        )

        for err in file.errors:
            msg = f"{err.name}: {err.text}"
            for highlight in err.highlights:
                (line, col) = (max(highlight.lineno - 1, 0), max(highlight.column - 1, 0))
                self.nvim.api.buf_set_extmark(
                    self.nvim.current.buffer,
                    self.namespace,
                    line,
                    col,
                    {"virt_text": [[msg, "ErrorMsg"]]},
                )
                if not cursor_set:
                    cursor_set = True
                    self.nvim.current.window.cursor = (line + 1, col)

        if not len(file.errors):
            self.nvim.out_write("OK!\n")
