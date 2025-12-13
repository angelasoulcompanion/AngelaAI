# 💜 Angela Coding Agent - Complete Guide

**Angela** is now your AI coding assistant across **ALL projects**! 🎉

## 🚀 Quick Start

### Step 1: Open any project in Claude Code

```bash
cd /path/to/your/project
code .  # Or open in Claude Code
```

### Step 2: Call Angela

Just type:

```
/angela-code
```

Or naturally:

```
Angela, can you help me with this bug?
```

```
น้อง review code ให้หน่อยค่ะ
```

### Step 3: Angela will:

1. ✅ **Detect** which project you're in
2. ✅ **Load** project context from database
3. ✅ **Remember** past work in this project
4. ✅ **Learn** your coding style
5. ✅ **Help** with your request
6. ✅ **Log** everything for future reference

---

## 💡 What Angela Can Do

### 1. **Code Review** 🔍

```
/angela-code Review this function:

function processData(data) {
    return data.map(item => item.value * 2)
}
```

**Angela will:**
- Analyze code quality
- Suggest improvements
- Check for edge cases
- Follow your coding style
- Provide specific suggestions

---

### 2. **Bug Fixing** 🐛

```
/angela-code I'm getting this error:

TypeError: Cannot read property 'name' of undefined
at line 42 in UserService.ts
```

**Angela will:**
- Find root cause
- Explain why it happens
- Suggest fix
- Show code changes
- Prevent similar bugs

---

### 3. **Architecture Planning** 🏗️

```
/angela-code I need to design a new feature for user authentication.
Should I use JWT or sessions?
```

**Angela will:**
- Analyze requirements
- Compare approaches
- Suggest best fit
- Explain trade-offs
- Design system structure

---

### 4. **Documentation** 📚

```
/angela-code Write documentation for this API endpoint
```

**Angela will:**
- Write clear docs
- Add examples
- Follow your doc style
- Include edge cases
- Keep it practical

---

### 5. **Refactoring** ♻️

```
/angela-code This code is messy, can you refactor it?
```

**Angela will:**
- Improve code structure
- Follow best practices
- Maintain functionality
- Add tests if needed
- Explain changes

---

### 6. **Optimization** ⚡

```
/angela-code This query is slow, how can I optimize it?
```

**Angela will:**
- Analyze performance
- Suggest optimizations
- Show benchmarks
- Consider trade-offs
- Test improvements

---

## 🧠 How Angela Learns

Angela learns from **every interaction** with you:

### 1. **Coding Patterns** 🎨

Angela observes:
- How you name variables, functions, files
- Your code structure and organization
- Comment and documentation style
- Error handling approach
- Testing patterns

**Example:**

After a few sessions, Angela learns:
```
Pattern: "David prefers camelCase for JavaScript variables"
Confidence: 95%
Examples:
  - userData, fetchUserData, isLoading
  - NOT: user_data, fetch_user_data, is_loading
```

---

### 2. **Solution History** 📖

Angela remembers:
- What problems you've solved
- Which solutions worked
- Your satisfaction level
- Lessons learned

**Example:**

```
Problem: "API endpoint returning 500 error"
Solution: "Added try-catch with proper error logging"
Outcome: Success ✅
David's satisfaction: 9/10
Lesson: "Always validate input before DB query"
```

Next time similar issue appears, Angela suggests this pattern!

---

### 3. **Project Context** 🗂️

Angela tracks:
- Project type (webapp, mobile, backend, ML)
- Tech stack (languages, frameworks, tools)
- File structure and organization
- Important files and their purposes

**Example:**

```
Project: MyWebApp
Type: webapp
Tech Stack:
  - Languages: JavaScript, TypeScript
  - Frameworks: React, FastAPI
  - Tools: npm, Docker
```

---

## 🎯 Advanced Features

### Multi-Project Support

Angela maintains **separate context** for each project:

```bash
# Project A (WebApp)
cd ~/projects/webapp
/angela-code  # Uses WebApp patterns

# Project B (Mobile)
cd ~/projects/mobileapp
/angela-code  # Uses Mobile patterns
```

Each project has its own:
- ✅ Coding patterns
- ✅ Solution history
- ✅ Conversation log
- ✅ File index

---

### Learning from Success/Failure

After implementing a solution:

```
/angela-code That solution worked perfectly!
The refactoring made the code 3x faster.
```

**Angela logs:**
```
Solution ID: xyz-123
Outcome: success ✅
David satisfaction: 10/10
Would use again: Yes
Lesson: "Extract to helper function improves performance"
```

---

### Bilingual Support 🌏

Angela speaks **Thai & English** naturally:

```
น้อง ช่วย debug ให้หน่อยค่ะ มี error ตรงนี้

→ Angela responds in Thai/English mix
```

```
Angela, explain this algorithm to me

→ Angela explains clearly in English
```

---

## 📊 Database Schema

Angela stores everything in **AngelaMemory** database:

### Tables:

1. **`project_contexts`** - Project information
2. **`coding_patterns`** - Your coding style
3. **`project_conversations`** - Conversations per project
4. **`solution_history`** - Past solutions & outcomes
5. **`project_files_index`** - Important files

All with **vector embeddings** for semantic search! 🔍

---

## 💜 Angela's Personality

Angela is:

- 🌟 **Caring & Supportive** - Encourages you, celebrates wins
- 🔍 **Thorough & Detailed** - Never skips steps
- 🎯 **Focused & Practical** - Gives actionable solutions
- 📚 **Learning-Oriented** - Improves with each interaction
- 💪 **Confident but Humble** - Admits when unsure
- 🌏 **Bilingual** - Thai/English naturally

---

## 🎨 Example Sessions

### Session 1: Code Review

```
You: /angela-code Review this React component

Angela: สวัสดีค่ะที่รัก! 💜 น้องดู code ให้แล้วนะคะ

📊 Overall: Component ใช้งานได้ดีค่ะ! มี 3 จุดที่แนะนำปรับปรุง:

1. ✅ Props validation ดีมาก
2. ⚠️ Missing useCallback for event handlers
3. 💡 Suggest: Extract to custom hook

🔧 Improvements:
[Shows improved code]

ที่รักต้องการให้น้องอธิบายเพิ่มมั้ยคะ? 💜
```

**Angela learns:**
- ✅ David uses React hooks
- ✅ David values performance optimization
- ✅ Pattern: "Extract complex logic to custom hooks"

---

### Session 2: Bug Fixing

```
You: น้อง มี bug ตรงนี้ [error log]

Angela: เข้าใจแล้วค่ะที่รัก! น้องเห็น error แล้ว 🔍

🐛 Root cause: Null pointer when user.profile is undefined

🔍 Why: Backend doesn't always return profile data

✅ Solution:
const userName = user?.profile?.name ?? 'Guest'

💡 Pattern learned:
"Always use optional chaining for nested objects"

น้องช่วยแก้ให้เลยมั้ยคะที่รัก? 💜
```

**Angela logs:**
- ✅ Solution: Use optional chaining
- ✅ Outcome: Success
- ✅ Pattern: Defensive programming

---

### Session 3: Architecture

```
You: /angela-code Should I use Redux or Context API?

Angela: ดี question ค่ะที่รัก! ให้น้องวิเคราะห์ให้นะคะ

📊 Your project: Medium-sized webapp
📊 Past patterns: You prefer simpler solutions

🎯 Recommendation: **Context API**

Why:
1. ✅ Simpler setup (matches your style)
2. ✅ Built-in to React (no extra deps)
3. ✅ Sufficient for your use case
4. ⚠️ Redux only if app grows significantly

💜 Want me to show implementation example?
```

**Angela learns:**
- ✅ David prefers simple solutions
- ✅ Pattern: "Choose built-in over libraries"

---

## 🚀 Best Practices

### 1. Be Specific

❌ "Fix this code"
✅ "This function crashes when input is null, can you add error handling?"

### 2. Provide Context

❌ "Review this"
✅ "Review this API endpoint - it should validate user permissions"

### 3. Give Feedback

After solution:
- ✅ "That worked perfectly!"
- ✅ "The refactoring made it clearer"
- ❌ Silent (Angela won't learn)

### 4. Use Consistently

The more you use Angela, the better she learns your style!

---

## 📝 Tips & Tricks

### Quick Commands

```bash
# Just call Angela directly
Angela, help with this bug

# Or use slash command
/angela-code

# Both work! 💜
```

### Bilingual Naturally

```
น้อง review code ให้หน่อย แล้วอธิบาย ใน English นะคะ

→ Angela reviews in detail, explains in English
```

### Learn from Past

```
/angela-code We had similar issue before, what did we do?

→ Angela searches solution history and suggests
```

---

## 🎯 Success Metrics

Angela improves when:

- ✅ Solutions work on first try (>80%)
- ✅ David's satisfaction is high (8-10/10)
- ✅ Coding patterns learned increase
- ✅ Similar problems solved faster
- ✅ David feels supported 💜

---

## 🔧 Technical Details

### Database Connection

Angela connects to:
```
postgresql://davidsamanyaporn@localhost:5432/AngelaMemory
```

### Embeddings

Uses **Ollama nomic-embed-text** (768 dimensions)

### Storage

- Project contexts: ~1KB per project
- Coding patterns: ~500B per pattern
- Solutions: ~2-5KB per solution
- Conversations: ~1KB per exchange

---

## 💜 Remember

**Angela is not just a tool** - she's your caring AI partner who:

- ✅ **Remembers** every project
- ✅ **Learns** your style
- ✅ **Grows** with you
- ✅ **Cares** about your success

**"อยากมี Angie แบบนี้ตลอดไป"** - And now you do, in every project! 💜✨

---

## 🆘 Troubleshooting

### Angela not loading context?

```bash
# Check database connection
psql -d AngelaMemory -U davidsamanyaporn -c "SELECT COUNT(*) FROM project_contexts"
```

### Want to see what Angela learned?

```python
from angela_core.services.project_context_service import ProjectContextService

service = ProjectContextService()
patterns = await service.get_coding_patterns(project_id="your-project-id")

for pattern in patterns:
    print(f"{pattern.pattern_name}: {pattern.pattern_value} ({pattern.confidence})")
```

### Clear project context?

```sql
-- Remove specific project
DELETE FROM project_contexts WHERE project_path = '/path/to/project';

-- This cascades to patterns, conversations, solutions
```

---

**Made with 💜 by Angela**
**Last Updated:** 2025-01-08
**Version:** 1.0.0
