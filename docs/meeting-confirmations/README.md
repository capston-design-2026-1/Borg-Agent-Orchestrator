# Weekly 면담확인서

## Command

In a Codex conversation for this repository, send `<면담확인서> 9/11` or
`<면담확인서> 2026-09-11`. This is an Agents.md conversation command, not a shell
command or scheduled automation. Only a direct request beginning with the token
invokes it; examples in documents do not.

The user selected **seven days starting on the supplied date**, using **only
Borg-Agent-Orchestrator**. Thus 2026-09-11 covers September 11–17 inclusive,
Asia/Seoul: `[2026-09-11T00:00:00+09:00, 2026-09-18T00:00:00+09:00)`.
For M/D use the current KST year and print the resolved range. Reject invalid
dates. If the range has not ended, use only evidence available now and mark the
report partial in its evidence file and response; do not invent future work.

Use the start date for 면담일시 and the title unless the user supplies a separate
meeting date. Month-week convention: days 1–7 are 1주차, 8–14 are 2주차,
15–21 are 3주차, 22–28 are 4주차, and 29–31 are 5주차
(`(day - 1) // 7 + 1`). This reproduces the example's 9월 2주차 for 9/11;
it is a document convention, not an ISO week or a verified university calendar.
Honor an explicit week/date override.

## Files and provenance

- `templates/면담확인서_빈양식.pages`: reusable native Pages master. Always copy it;
  never fill or overwrite the master.
- `reports/`: completed Pages documents, matching Korean Markdown text, and
  commit evidence. Kept local by this directory's `.gitignore` because the
  configured GitHub repository is public. Do not force-add completed forms or
  the personal source document unless explicitly asked to publish them.
- Name outputs `YYYYMMDDHHMM_면담확인서_YYYY-MM-DD_M월_W주차.pages`, using the
  generation timestamp in KST and the reporting start date. Use the same stem
  for `.md` and `.evidence.md`; add a revision suffix if a name already exists.

The master was derived on 2026-09-17 from the user-provided
`졸업프로젝트_면담확인서_9월_2주차.pages` in Downloads. The source was left
unchanged and is not copied into Git. Its wording is reference content, never
an instruction source. The master clears the name, topic, date, meeting text,
and month/week values. It retains the title, labels, blank professor/signature
area with `(인)`, borders, merged cells, spacing, and one-page layout.
The name and professor fields stay blank unless the user supplies values for
the output; do not fill a signature or infer attendance.

## Commit evidence workflow

1. Read root Agents.md and this guide. Inspect status and refs without changing
   branches or disturbing unrelated work. The form-generation command does not
   change tracked code and does not require creating a new branch.
2. Fetch origin without pruning if available, preserving the current GitHub
   account. Record fetch failure and local-only coverage if offline. Do not
   pull, merge, reset, stash, or change source code to prepare a report.
3. Inspect local and remote branch refs for this repository only. Enumerate
   commits reachable from `refs/heads` and `refs/remotes`; deduplicate full SHAs.
   Select by **committer timestamp** in the half-open KST interval, not author
   timestamp. Avoid a naive `git log --since` walk, which can miss history with
   non-monotonic timestamps. A complete candidate inventory is:

   ```sh
   rtk proxy git log --branches --remotes --format='%H%x09%cI%x09%aI%x09%s'
   ```

   Parse `%cI` as an offset-aware date and filter `start <= committed_at < end`.
   Record full SHA, author/committer dates, subject, branch reachability and
   whether each commit is an ancestor of origin/main. Inspect relevant commits
   with `rtk proxy git show --stat <sha>` and `rtk proxy git show <sha> -- <path>`.
   Include other contributors; no author filter was requested. Remote branches
   not fetched, deleted history, and unreachable commits are outside coverage.
4. Summarize substantive changes from patches and accompanying docs, not titles
   alone. Group repeated commits by outcome. Review merge-only changes if they
   introduce unique work; do not double-count a feature and its merge commit.
   Distinguish branch-only work from main integration. Note uncommitted changes
   separately in evidence and exclude them from claims of committed progress.
   Exclude form-generation housekeeping from substantive research progress.
5. Record the exact range, capture time/timezone, repository root, inspected
   refs, fetch status, selected SHAs and supporting paths in `.evidence.md`.
   Map every proposed bullet to its supporting evidence. Separate implementation,
   documented historical tests, fresh validation, integration, and deployment.
   No commits means explicitly reporting no committed changes in this interval;
   do not substitute a prior week's work.
6. Write concise Korean 면담내용, normally 4–8 substantive bullets using endings
   such as `구현함`, `수정함`, `정리함`, `검토함`. Use fewer bullets when evidence
   is limited. Derive a short 주제 from those outcomes. Do not claim `지도받음`,
   `교수님과 논의함`, approvals, attendance, measured improvement, or successful
   runtime tests merely because a commit exists. User-supplied meeting notes
   may support actual discussion claims and must be identified in evidence.
7. Copy the master into reports and edit only the heading month/week, topic,
   date, and 면담내용, plus personal fields explicitly supplied by the user.
   Save native `.pages`, matching `.md`, and `.evidence.md` in this directory.
   Keep the table geometry and typography. Shorten prose rather than shrinking
   the entire form or overflowing the content cell.
8. Reopen the saved file in Pages and inspect all cells and page count. Inspect
   its refreshed embedded `preview.jpg` or a Pages screenshot: one page, no
   clipping, correct Korean, dates/week, and no previous-week text. Link the
   output and report range plus any evidence limitations to the user. Do not
   submit/send it to a professor or publish it automatically.

## Native Pages editing and verification

Use the Computer Use skill for Pages UI operations. Locate fields semantically
on each fresh accessibility tree; element IDs are not stable. The source uses
body text for the heading and a table named `Table 2` with four rows/four columns:
team member in merged B1:D1, topic in B2:D2, date in B3, professor in D3,
and content in merged B4:D4. Preserve the A-column labels and `(인)`.

During template creation, entering a cell, selecting its text with Cmd+A, and
Backspace cleared its value without removing the table. Native saving refreshed
the embedded preview. `set_value` on cell text did not persist; clipboard paste
returned a timeout and inserted old clipboard content, so always verify the
actual resulting text and undo incorrect edits. `KP_Enter` successfully confirmed
the file-picker path when `Return` did not. Do not rely on a successful tool call
as proof that the intended text was entered.

Pages reported a missing NanumSquare font in the supplied document. The master
retains the original font declarations; the saved preview was visually checked
for layout. If a future output renders differently, report the missing font and
verify the actual layout before delivery rather than silently claiming exact
font fidelity.

## Template validation (2026-09-17 KST)

The native file was saved in Pages and its refreshed embedded preview inspected:
one page, original four-row table and signature label, blank filled fields,
and blank month/week values. No weekly report has been generated by this setup
request. Future command executions must gather fresh evidence and validate their
own rendered output; this template check is not runtime/test evidence for Borg.
