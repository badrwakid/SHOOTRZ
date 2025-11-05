# Pass 6-7 Code Quality Execution Plan

**Created**: October 20, 2025  
**Status**: ⏸️ READY TO EXECUTE (Awaiting Confirmation)  
**Risk Level**: LOW-MEDIUM (Formatting only, no logic changes)

---

## 📊 Scope Analysis

### Files to be Modified:
- **Frontend**: 51 TypeScript/TSX files
- **Backend**: 21 Python files
- **Total**: 72 files will be formatted

### What Will Change:
✅ **Formatting ONLY** - No logic changes
- Consistent indentation
- Quote style (single vs double)
- Line length limits
- Trailing commas
- Spacing around operators

### What Will NOT Change:
❌ No functionality changes
❌ No variable renames
❌ No structural refactoring
❌ No import changes (unless unused)

---

## 🛡️ Safety Measures

### Pre-Execution Backup:
1. **Create snapshot**: `__graveyard__/pass-6-7-backup/`
2. **Copy all source**: Before any formatting

### Validation Gates:
1. ✅ Backend must start: `python backend/app.py`
2. ✅ Frontend must compile: `npm start`
3. ✅ TypeScript must validate: `tsc --noEmit`
4. ✅ No new errors introduced

### Rollback Strategy:
- Option 1: Restore from `__graveyard__/pass-6-7-backup/`
- Option 2: Git revert if committed
- Option 3: Use diff to review each change

---

## 📋 Pass 6: Frontend (TypeScript/React Native)

### Step 1: Install Dev Dependencies
```bash
cd basketball-training-app
npm install --save-dev eslint prettier eslint-plugin-prettier eslint-config-prettier @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

**Risk**: LOW - Only installs dev dependencies, doesn't affect runtime

### Step 2: Create Configuration Files

**File 1: `.prettierrc`**
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always"
}
```

**File 2: `.eslintrc.js`**
```javascript
module.exports = {
  root: true,
  extends: [
    'expo',
    'plugin:@typescript-eslint/recommended',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'prettier'],
  rules: {
    'prettier/prettier': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
    'no-console': 'off',
  },
};
```

**Risk**: LOW - Config files don't change code

### Step 3: Add NPM Scripts

Update `package.json` scripts section:
```json
"scripts": {
  "start": "expo start",
  "android": "expo start --android",
  "ios": "expo start --ios",
  "web": "expo start --web",
  "lint": "eslint . --ext .ts,.tsx",
  "lint:fix": "eslint . --ext .ts,.tsx --fix",
  "format": "prettier --write \"src/**/*.{ts,tsx}\"",
  "format:check": "prettier --check \"src/**/*.{ts,tsx}\"",
  "typecheck": "tsc --noEmit"
}
```

**Risk**: LOW - Only adds commands, doesn't run them

### Step 4: Create Backup
```bash
# Create full backup of src/
cp -r src __graveyard__/pass-6-7-backup/src-original
```

**Risk**: NONE - Safety measure

### Step 5: Run Prettier (DRY RUN FIRST)
```bash
npm run format:check
```
This shows what WOULD change without changing it.

**Risk**: NONE - Read-only check

### Step 6: Run Prettier (ACTUAL FORMATTING)
```bash
npm run format
```
This applies formatting to all 51 TypeScript files.

**Expected Changes**:
- Quotes: double → single
- Semicolons: added where missing
- Indentation: standardized to 2 spaces
- Line breaks: consistent
- Trailing commas: added in multiline

**Risk**: LOW - Formatting only, syntax unchanged

### Step 7: Validate TypeScript
```bash
npm run typecheck
```
Ensures no TypeScript errors introduced.

**Risk**: NONE - Validation only

### Step 8: Test Compilation
```bash
npm start
```
Verify frontend compiles without errors.

**Expected**: Should compile identically, just with cleaner code.

**Risk**: LOW - If errors occur, rollback available

---

## 📋 Pass 7: Backend (Python/Flask)

### Step 1: Create Configuration

**File: `backend/pyproject.toml`**
```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
skip-string-normalization = false
skip-magic-trailing-comma = false

[tool.ruff]
line-length = 100
target-version = "py38"
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "W",   # pycodestyle warnings
    "I",   # isort
]
ignore = [
    "E501",  # line too long (handled by black)
]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

**Risk**: LOW - Config files don't change code

### Step 2: Activate Virtual Environment
```bash
cd backend
.\venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Mac/Linux
```

**Risk**: NONE - Just activating venv

### Step 3: Install Formatting Tools
```bash
pip install black ruff mypy
```

**Risk**: LOW - Only installs dev tools in venv

### Step 4: Create Backup
```bash
# Backup all Python files
mkdir -p ../__graveyard__/pass-6-7-backup/backend-original
cp *.py ../__graveyard__/pass-6-7-backup/backend-original/
```

**Risk**: NONE - Safety measure

### Step 5: Run Black (DRY RUN FIRST)
```bash
black . --check --diff
```
Shows what WOULD change without changing it.

**Risk**: NONE - Read-only check

### Step 6: Run Black (ACTUAL FORMATTING)
```bash
black .
```
Formats all 21 Python files.

**Expected Changes**:
- Quotes: standardized to double quotes
- Line length: wrapped at 100 chars
- Indentation: standardized to 4 spaces
- Spacing: consistent around operators
- Blank lines: standardized

**Risk**: LOW - Formatting only, syntax unchanged

### Step 7: Run Ruff (Linting)
```bash
ruff check . --fix
```
Fixes import sorting and minor issues.

**Risk**: LOW - Only safe auto-fixes

### Step 8: Validate Python Syntax
```bash
python -m py_compile app.py
```
Ensures no syntax errors.

**Risk**: NONE - Validation only

### Step 9: Test Backend
```bash
python app.py
```
Verify backend starts without errors.

**Expected**: Should start identically, just with cleaner code.

**Risk**: LOW - If errors occur, rollback available

---

## 📝 Post-Execution Validation Checklist

### Must Pass Before Accepting:
- [ ] Backend starts successfully (`python backend/app.py`)
- [ ] Backend responds to health check (`curl http://localhost:5000/health`)
- [ ] Frontend compiles without errors (`npm start`)
- [ ] TypeScript validation passes (`npm run typecheck`)
- [ ] No new ESLint errors introduced
- [ ] No syntax errors in Python files
- [ ] Git diff shows ONLY formatting changes (no logic)

### Review Before Committing:
- [ ] Spot-check 3-5 files to ensure changes are formatting only
- [ ] Verify no functionality removed
- [ ] Confirm no imports broken
- [ ] Check that strings/comments unchanged (content-wise)

---

## 🚨 Red Flags (Stop & Rollback If Seen)

❌ **Backend won't start** → Rollback immediately  
❌ **Frontend compile errors** → Rollback immediately  
❌ **TypeScript type errors** → Review carefully  
❌ **Import errors** → Rollback immediately  
❌ **Tests fail** (if any exist) → Investigate  
❌ **Functionality changed** → Rollback immediately  

---

## 📊 Expected Outcomes

### Frontend:
✅ Consistent quote style (single quotes)  
✅ Consistent indentation (2 spaces)  
✅ Consistent semicolon usage  
✅ Cleaner, more readable code  
✅ ESLint warnings reduced  

### Backend:
✅ Consistent quote style (double quotes)  
✅ Consistent indentation (4 spaces)  
✅ Line length maintained (100 chars)  
✅ Import sorting (alphabetical)  
✅ PEP 8 compliance  

### Repository:
✅ Professional code quality  
✅ Easier to onboard new developers  
✅ Consistent style across team  
✅ Better git diffs (less noise)  

---

## 🔄 Rollback Instructions

### If Something Goes Wrong:

**Option 1: Restore from Backup**
```bash
# Frontend
rm -rf src
cp -r __graveyard__/pass-6-7-backup/src-original src

# Backend
rm backend/*.py
cp __graveyard__/pass-6-7-backup/backend-original/*.py backend/
```

**Option 2: Git Revert** (if changes committed)
```bash
git revert HEAD
```

**Option 3: Manual Review**
```bash
# Review changes file by file
git diff HEAD~1 HEAD

# Restore specific file
git checkout HEAD~1 -- path/to/file.ts
```

---

## ⏱️ Estimated Time

- **Pass 6 (Frontend)**: 5-10 minutes
  - Install deps: 2 min
  - Config: 1 min
  - Format: 1 min
  - Validate: 2-5 min

- **Pass 7 (Backend)**: 5-10 minutes
  - Install deps: 1 min
  - Config: 1 min
  - Format: 1 min
  - Validate: 2-5 min

- **Total**: 10-20 minutes

---

## ✅ Execution Decision

**Recommendation**: PROCEED with caution

**Why Safe**:
1. All changes are formatting only
2. Multiple validation gates
3. Full backup before execution
4. Easy rollback available
5. No logic changes

**Why Execute Now**:
1. Establishes code quality baseline
2. Makes future PRs cleaner
3. Better developer experience
4. Industry best practice

**When to Execute**:
- ✅ Now: If you want professional code quality
- ⏸️ Later: If actively debugging or in middle of feature
- ❌ Never: If code style doesn't matter (not recommended)

---

## 🎯 Final Confirmation Required

**I am ready to execute Passes 6-7 with the following understanding:**

1. ✅ 72 files will be reformatted (51 TS + 21 Python)
2. ✅ Only formatting changes, no logic changes
3. ✅ Full backup will be created first
4. ✅ Multiple validation gates will run
5. ✅ Easy rollback if anything breaks
6. ✅ Estimated time: 10-20 minutes

**Proceed with execution?**

Type **"PROCEED"** to execute both passes  
Type **"SKIP"** to document and defer  
Type **"REVIEW"** to see sample changes first  





