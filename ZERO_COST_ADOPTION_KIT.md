# T-Zero: %100 Bedava Açık Kaynak Yaygınlaştırma Kiti (Zero-Cost Roadmap)

> **Maliyet Garantisi:** Bu plandaki tüm adımlar **%100 BEDAVADIR (0.00 TL / $0.00)**.
> Hiçbir reklam, hiçbir sponsorlu içerik, hiçbir kredi kartı veya ödeme gerektirmez.

---

## 1. Küratörlü MCP Dizinlerine Kayıt (Ücretsiz PR & Dizinler)

Geliştiriciler yeni MCP sunucularını doğrudan açık kaynak listelerinden keşfeder.

### A. `awesome-mcp-servers` GitHub PR (Aktif & Doğrulandı)
- **Hedef Repo:** `https://github.com/punkpeye/awesome-mcp-servers`
- **Mevcut PR Durumu:** **Açık (PR #15852)**  
  URL: [https://github.com/punkpeye/awesome-mcp-servers/pull/15852](https://github.com/punkpeye/awesome-mcp-servers/pull/15852)  
  Etiketler: `valid-name`, `has-glama`, `has-emoji`  
  Maliyet: **0.00 TL / $0.00**

İçerik:
```markdown
- [T-Zero](https://github.com/toprakahmetaydogmus/TZeroAlgorithm) - Enterprise-grade AST context tree builder & token reducer for coding agents (up to 94.9% context token reduction, 16 MCP tools).
```

### B. Glama MCP Registry (Ücretsiz Web Listeleme)
- **Adres:** `https://glama.ai/mcp/servers`
- **Maliyet:** 0$ (Açık kaynak repolar için ücretsiz dizin)
- **İşlem:** GitHub hesabıyla giriş yapıp repo linkini (`toprakahmetaydogmus/TZeroAlgorithm`) ekleyin.

### C. PulseMCP (Ücretsiz Topluluk Dizini)
- **Adres:** `https://pulsemcp.com`
- **İşlem:** "Submit Server" butonuna tıklayıp GitHub linkini ve `smithery.json` referansını gönderin.

---

## 2. Hacker News: "Show HN" Teknik Gönderisi (Ücretsiz)

Hacker News geliştiricileri reklam dilinden nefret eder, somut mühendislik detaylarına saygı duyar.

- **Başlık (Title):**
  ```text
  Show HN: T-Zero – AST Context Pruner for MCP Coding Agents (94% Token Reduction)
  ```
- **İçerik (Metin):**
  ```text
  Hi HN,

  I built T-Zero (https://github.com/toprakahmetaydogmus/TZeroAlgorithm) to solve a concrete failure mode in autonomous coding agents: context choke.

  When an agent ingests an entire repository naively, the quadratic cost of self-attention wastes tokens on internal imperative loop bodies that the agent rarely needs for structural reasoning. As transcripts blow past 50k tokens, instruction-following fidelity drops significantly.

  T-Zero is an MCP server (with stdio transport and CLI) that performs multi-tier AST pruning:
  - T-1 (Signatures & Types): Strips implementations, keeps class hierarchies, function signatures, docstrings, and type contracts.
  - T-2 (Interfaces & Call Graphs): Keeps structural architectural boundaries while pruning local variables.
  - T-3/T-4: High-level architectural topologies and semantic AST symbol mapping.

  In a baseline test on real-world repositories (e.g. 56,000 raw tokens), T-Zero pares down the payload to ~3,200 tokens without losing class relationships or public interfaces.

  It runs completely locally via Python (no cloud embedding calls, zero data leakage), supports MCP stdio transport for Cursor, Windsurf, Claude Desktop, and Gemini CLI, and includes an AST static auditor for secrets and code smells.

  Quickstart:
  pip install tzero-mcp

  Or configure in Claude Desktop / Cursor / Antigravity:
  {"mcpServers": {"tzero": {"command": "tzero-mcp"}}}

  Source code is open under MIT:
  https://github.com/toprakahmetaydogmus/TZeroAlgorithm

  I would appreciate technical critiques on the AST heuristics and edge cases.
  ```

---

## 3. Topluluklarda Organik Sorun Çözümü (Reddit / Discord)

Reddit (`r/LocalLLaMA`, `r/Cursor`, `r/ClaudeAI`) topluluklarında insanlar context window dolması veya token maliyetlerinden şikayet ettiğinde paylaşılabilecek teknik yanıt:

```text
The issue with feeding raw source files to coding agents is that LLM attention heads get cluttered with internal loop bodies rather than high-level interface boundaries.

If you are running into context choke or token limits, try AST-based pruning instead of raw file reads. We open-sourced an MCP tool called T-Zero (https://github.com/toprakahmetaydogmus/TZeroAlgorithm) that strips out function bodies and leaves class structures, signatures, and types intact. In typical repos it cuts token load by ~90% while keeping the architecture intact for the agent.
```

---

## 4. Terminal Görsel Kanıtı (Görsel > Metin)

Geliştiricilere "94% azalttık" demek yerine 15 saniyelik terminal kaydı gösterilir:
1. `demo.tape` dosyası hazırlandı (Charm VHS - %100 açık kaynak).
2. `vhs demo.tape` çalıştırıldığında ücretsiz olarak `demo.gif` üretir.
3. README'nin en üstüne bu GIF eklendiğinde gelen mühendis anında ne işe yaradığını anlar.
