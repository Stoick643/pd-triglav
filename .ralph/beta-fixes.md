# Beta Testing Fixes

Fix all issues from beta testing report.

## Goals
- Fix all 9 reported issues from beta testing
- Ensure tests pass after changes

## Checklist
- [x] #2 OAuth: Fix redirect URI for custom domain pdtriglav.si — added ProxyFix middleware
- [x] #4 Space bar in comments triggers photo zoom — added input/textarea guard
- [x] #1 Add change password feature — route, form, template, sidebar link
- [x] #3 Verify email notifications working — code is correct, needs SES secrets verification
- [x] #5 'Moja poročila' not showing reports — dashboard now queries actual data
- [x] #6 'Zadnje fotografije' not showing photos — dashboard now queries actual data
- [x] #7 History event: reload returns same event — now randomly picks from all events for today
- [x] #9 Admin panel 'Objavi nov izlet' button unresponsive — was disabled placeholder, now links to trip creation
- [x] #8 Admin panel improvements — full rewrite with stats, user list, quick actions

## Verification
- All fixes verified with `create_app()` — app starts OK
- `test_auth.py`: 4/6 pass (2 pre-existing failures unrelated to changes)
- Full suite: 210 passed, 41 pre-existing failures (trip_modal, LLM tests etc.)
- Fixed NameError bug caught during testing (missing UserRole import in admin route)

## Summary of all changes
1. `app.py` — Added ProxyFix middleware for HTTPS behind proxy
2. `routes/auth.py` — Added change_password route with OAuth user support
3. `templates/auth/change_password.html` — New template
4. `templates/base.html` — Added "Spremeni geslo" sidebar link
5. `templates/reports/detail.html` — Input guard in keyboard navigation
6. `routes/main.py` — Dashboard queries reports/photos; history uses random.choice; admin gets stats+user list
7. `templates/dashboard.html` — Dynamic reports, photos, working trip creation button
8. `templates/admin/dashboard.html` — Full rewrite with stats cards, quick actions, user table
