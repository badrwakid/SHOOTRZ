# Passes 6-7: Code Quality - DEFERRED (Future Enhancement)

## Status: DOCUMENTED FOR FUTURE

These passes require installing dev dependencies and running formatters, which is best done when actively developing.

## Pass 6: Frontend Code Quality

### To Do:
1. Create `.prettierrc`:
   ```json
   {
     "semi": true,
     "singleQuote": true,
     "tabWidth": 2,
     "trailingComma": "es5"
   }
   ```

2. Create `.eslintrc.js`:
   ```javascript
   module.exports = {
     extends: ['expo', 'prettier'],
     plugins: ['prettier'],
     rules: {
       'prettier/prettier': 'error',
       '@typescript-eslint/no-unused-vars': 'warn',
     },
   };
   ```

3. Install dev dependencies:
   ```bash
   npm install --save-dev eslint prettier eslint-plugin-prettier eslint-config-prettier
   ```

4. Add scripts to `package.json`:
   ```json
   "lint": "eslint . --ext .ts,.tsx",
   "format": "prettier --write \"src/**/*.{ts,tsx}\"",
   "typecheck": "tsc --noEmit"
   ```

5. Run: `npm run format` then `npm run lint --fix`

## Pass 7: Backend Code Quality

### To Do:
1. Create `backend/pyproject.toml`:
   ```toml
   [tool.black]
   line-length = 100
   target-version = ['py38']
   
   [tool.ruff]
   line-length = 100
   select = ["E", "F", "W", "I"]
   ignore = ["E501"]
   ```

2. Install in venv:
   ```bash
   pip install black ruff mypy
   ```

3. Run formatters:
   ```bash
   black backend/
   ruff check backend/ --fix
   ```

4. Add type hints to key functions
5. Remove debug print statements

## Why Deferred:

1. **Time**: Formatting large codebase takes time
2. **Review**: Changes should be reviewed before committing
3. **Active Dev**: Best done during active development cycles
4. **Not Blocking**: Code works fine without formatting
5. **Audit Focus**: Current audit focused on structure and dead code

## Recommendation:

Run these passes before next major release or when setting up CI/CD pipeline.

## Risk Level: LOW
- Formatting doesn't change logic
- Can be done incrementally
- Easy to review in PR

## Current Status: ✅ DOCUMENTED
- Instructions ready
- Can be executed anytime
- No blocker to deployment





