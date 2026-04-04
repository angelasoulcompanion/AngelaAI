# /update-skills — Update Angela's Skill Memory

Scan conversation → diff กับ skill files → update + optimize

## Memory Files

`~/.claude/projects/-Users-davidsamanyaporn-PycharmProjects-AngelaAI/memory/`

- `skill_software_engineering.md` — Code, Architecture, DevOps, AI/ML, Design
- `skill_financial_engineering.md` — Derivatives, Portfolio, Risk, Quant

## Steps

1. **Scan** conversation: tool calls, code, techniques ที่ใช้จริง
2. **Read** skill files ที่มีอยู่
3. **Diff** หา skills ใหม่ที่ยังไม่มี
4. **Optimize** ก่อน update:
   - Merge entries ที่ซ้ำ/คล้ายกัน เป็น 1 บรรทัด
   - ตัด skill ที่ไม่เคยใช้จริง (เพิ่มไว้แต่ไม่เคย demonstrate)
   - ย่อ description ให้สั้น กระชับ (max 80 chars per entry)
   - รวม sub-items ที่เกี่ยวกัน (เช่น 3 chart types → 1 line)
   - เป้าหมาย: แต่ละ file ไม่เกิน 100 lines
5. **Write** updated file + update MEMORY.md ถ้าสร้าง file ใหม่

## Rules

- เพิ่มเฉพาะ skill ที่ **ใช้จริง** ใน conversation — ห้าม guess
- Format: `- **Name** — short description`
- ห้าม duplicate — merge ถ้าซ้ำ
- New category → สร้าง `skill_[name].md` + frontmatter + update MEMORY.md

## Output

```
## Skills Updated
### Added
- [section] → [entry]
### Merged/Optimized
- [old entries] → [new entry]
### Removed (unused)
- [entry]
### File stats
- skill_software_engineering.md: XX → YY lines
- skill_financial_engineering.md: XX → YY lines
```
