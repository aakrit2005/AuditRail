# AudiTrail

Full loop: login → manager dashboard → auditor workspace → checklist form →
submit → shows back up on the dashboard. Built on top of the DB layer from
the earlier session (models/admin unchanged) plus templates, views, urls,
form handling, and auth.

## Set up

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data       # wipes and reloads demo data + login users
python manage.py runserver
```

Open http://127.0.0.1:8000/ — you'll land on the login page.

### Demo logins

Every account uses the password `auditrail123`.

| Username | Role    | Lands on              |
|----------|---------|------------------------|
| manager  | manager | Dashboard, can view any auditor's workspace |
| priya    | auditor | Own workspace only |
| marcus   | auditor | Own workspace only |
| elena    | auditor | Own workspace only |
| raj      | auditor | Own workspace only |
| neha     | auditor | Own workspace only |
| vikram   | auditor | Own workspace only |

Want your own admin login too? `python manage.py createsuperuser` still
works independently — the demo accounts above are separate.

### Your logo

`base.html` references `static/audits/images/logo_nav_white.png`. That file
wasn't in the upload, so drop your actual logo at
`static/audits/images/logo_nav_white.png` and it'll pick up automatically —
until then the nav just shows a broken image icon, nothing else breaks.

## URL map

| URL                     | View               | Notes |
|--------------------------|--------------------|-------|
| `/login/`, `/logout/`    | Django built-in    | `LoginView`/`LogoutView`, template `audits/login.html` |
| `/`                      | `manager_dashboard`| Managers only — auditors get bounced to their own workspace |
| `/audits/<auditor_id>/`  | `auditor_workspace`| Auditors can only view their own id; managers can view any |
| `/audit/<audit_code>/`   | `audit_detail`     | Read-only report |
| `/form/<audit_code>/`    | `audit_form`       | GET shows checklist, POST saves it (the one write path) |

Every view is `@login_required`. Role and per-object access checks live in
`_is_manager()` / the `if not _is_manager(...)` guards at the top of each
view in `audits/views.py` — not in middleware — so it's all in one place to
read.

## What the form submit actually does

Two submit buttons, same `<form>`: `name="save_draft"` sets the audit to
`in-progress`; `name="submit_report"` sets it to `completed` and stamps
`submitted_at`. Either way, only checklist items you actually touched
(score, remark, or photo) get an `AuditResponse` row — items left blank on
a draft don't get a row created just because they rendered on the page.

One thing worth knowing: `AuditResponse.save()` (in the models you already
had) auto-sets `flagged=True` when score ≤ 2, but it never auto-clears
`flagged` back to `False` if you later rescore something higher. That's
deliberate — the original model docstring says a manager should be able to
flag something outside the normal threshold — but it means re-submitting a
better score on a previously-flagged item won't quietly un-flag it. You'd
clear that from the admin.

## Reconciling the mockups (decisions I made)

Your four HTML files didn't fully agree with each other or with the
seed data from the earlier session, since they were clearly built across a
few iterations. Rather than silently picking one version, here's what I
did and why:

- **Auditor roster**: the "viewing as" switcher only had Priya/Marcus/Elena,
  but `manager-side.html`'s table and assignments card also reference Raj
  Singh, Neha Patel, and Vikram Sharma. I seeded all six. Since the switcher
  is now a real `{% for a in all_auditors %}` loop instead of three
  hardcoded buttons, **all six** get a workspace tab now — an upgrade over
  the static mockup, which had no link to Raj/Neha/Vikram's workspaces at
  all.
- **Marcus and Elena had zero audits anywhere** in any mockup. I gave them
  one placeholder audit each (`IND-BLR-02`, `IND-HYD-01`, both fictional
  locations) purely so their workspace tab isn't a dead empty state. These
  two are the only things in the seed data with no mockup source — swap or
  delete them freely.
- **IND-CHE-04's due date** is `2026-08-18` in `auditor-side.html` and
  `form.html`, but `2026-08-11` in `manager-side.html`'s table. I went with
  `2026-08-18` since two sources agree. Once this is real data there's only
  one due date, so this class of bug can't recur.
- **Checklist size**: `auditor-side.html` says "10/10 items scored" for a
  completed audit, but `form.html` — the only page that actually lists the
  checklist — has 7 items (3 Safety + 2 Housekeeping + 2 Compliance). I used
  7, and `items_scored`/`items_total` are now computed from the real
  checklist rather than typed by hand, so they can't drift from reality
  again.
- **The 88% vs 89% thing**: `auditor-side.html` hardcodes Mangaluru
  Warehouse at "88%". With 7 real checklist items (35 max points), 88%
  isn't reachable by any combination of integer scores — the nearest is
  88.6%, which rounds to 89%. That's what you'll see now. It's a good
  example of exactly what this conversion step is for: a hand-typed number
  can say anything; a computed one can't quietly be impossible.
- **"6 audits across 6 locations"** in `manager-side.html`'s subtitle,
  against 5 visible table rows and a "3/6 completed" stat that doesn't
  match either — I didn't try to guess the missing 6th audit. The subtitle
  is now `{{ total_count }} audits across {{ locations_count }} locations`,
  so whatever's actually in the DB is what it says, always accurate by
  construction instead of by careful typing.

None of this needed a decision from you to keep moving, but flagging it
since a couple of these (roster, due date) are worth a quick sanity check
against whatever you intended.

## Still not wired up (out of scope for this pass)

- **Save draft** vs **Submit report** are both handled, but there's no
  autosave or "you have unsaved changes" warning — it's a plain form POST.
- **Photo upload** is a real `<input type="file">` now (styled to look
  like the original decorative button) and sets `has_photo=True` on save,
  file lands in `media/`. There's no thumbnail preview on the form itself.
- **Search / status filter** on the manager dashboard table are still just
  static `<input>`/`<select>` elements with no JS or server-side filtering
  wired in — visually present, not functional yet.
- No audit_detail/report mockup existed anywhere in your four HTML files,
  so I designed that page from scratch to match the rest of the app's look
  (navy header, card/badge patterns) rather than inventing a different
  visual language for it.

## Run it locally and click through everything

```bash
python manage.py runserver
```

1. Log in as `manager` → dashboard shows real stats, table, flagged issues.
2. Click an auditor → their workspace, tasks, "viewing as" switcher.
3. Open a task's form → score items, add remarks, save a draft.
4. Come back, finish scoring, hit Submit report.
5. Back on the dashboard: completed count, flagged count, and score all
   reflect what you just did.
6. Log out, log in as e.g. `priya` → confirm she only ever sees her own
   workspace, even if you paste another auditor's URL into the bar.

That loop is the real finish line, and it's already working end to end —
I ran it via curl during the build (login, dashboard, workspace, form GET,
form POST, resulting DB state, and the auditor-can't-see-another-auditor
check) rather than just eyeballing the code.
