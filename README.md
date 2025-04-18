# c-formatter-42.nvim

## Installation

### Prerequisites

- If you're not using venv, I would recommend creating one
```bash
mkdir -p ~/.local/venv && cd ~/.local/venv
python3 -m venv nvim
nvim/bin/pip install -U pynvim c-formatter-42 norminette
```
- Then in your init.lua
```lua
vim.g.python3_host_prog = vim.env.HOME .. '/.local/venv/nvim/bin/python'
```

### Plugin manager

lazy.nvim:
```lua
{
  'playwmadness/c-formatter-42.nvim',
  build = { ':UpdateRemotePlugins' },
}
```

## Usage

`:Norminette` to populate diagnostics for current file

`:CFormatNorm` to run the current file through c-formatter-42
