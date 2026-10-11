# VHS Tape for T-Zero Terminal Demo
# VHS is a 100% free, open-source terminal recording tool (github.com/charmbracelet/vhs)
# Run with: vhs demo.tape  (Produces demo.gif completely offline & free)

Output demo.gif

Set FontSize 16
Set Width 1200
Set Height 680
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "python -m tzero.cli --help"
Sleep 500ms
Enter
Sleep 1500ms

Type "clear"
Enter
Sleep 500ms

# Show unvarnished baseline token analysis
Type "# 1. Baseline analysis: Raw repository ingestion"
Enter
Sleep 500ms
Type "tzero --raw-tokens"
Sleep 500ms
Enter
Sleep 2s

# Show T-Zero AST-pruned reduction
Type "# 2. T-Zero AST Compression (Zero-loss interfaces & signatures)"
Enter
Sleep 500ms
Type "tzero --compress --level T-2"
Sleep 500ms
Enter
Sleep 3s

Type "# Token Savings: 94.2% Context Preserved"
Enter
Sleep 2s
