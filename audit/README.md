# Dependency Audit - November 2025

This directory contains the comprehensive dependency audit report for the `/apps/web` Next.js application.

## Files

- **dependency-report.md** - Full audit report with inventory, risk assessment, and upgrade plan

## Summary of Changes (Phase 1)

### ✅ Completed in This PR

1. **Removed Deprecated Package**
   - Removed `@supabase/auth-helpers-nextjs` from both root and web package.json
   - Already replaced by `@supabase/ssr`

2. **Added Engine Requirements**
   - Set Node.js requirement: `>=18.18.0`
   - Set pnpm requirement: `>=8.10.0`

3. **Updated Low-Risk Dependencies**
   - `@types/node`: 20.10.6 → 20.19.24
   - `@types/react`: 18.2.46 → 18.3.26
   - `@types/react-dom`: 18.2.18 → 18.3.7
   - `lucide-react`: 0.294.0 → 0.552.0
   - `tailwind-merge`: 2.2.0 → 3.3.1
   - `lint-staged`: 15.2.0 → 16.2.6

4. **Added Automation**
   - Configured Renovate bot (`.github/renovate.json`)
   - Added CI workflow for security audits (`.github/workflows/web-ci.yml`)

### Security Status

- ✅ No high/critical vulnerabilities
- ✅ All security audits passing
- ✅ No deprecated packages in use

### Known Issues

- ⚠️ Pre-existing build failure: Missing `@/lib/discovery` module
  - This is unrelated to dependency updates
  - Needs to be addressed separately

## Next Steps (Future PRs)

1. **Phase 2:** Upgrade to Next.js 15.x (keep React 18)
2. **Phase 3:** Migrate to ESLint 9
3. **Phase 4:** Consider React 19 + Next.js 16 upgrade
4. **Phase 5:** Plan Tailwind CSS v4 migration

See the full report for detailed migration guides and risk assessment.
