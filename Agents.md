# Repository Instructions

These instructions apply to work performed in this repository.

## Workflow Defaults

- Continue to the next logical engineering step unless the user explicitly tells you to stop or redirect.
- Make code changes directly rather than stopping at analysis when the next implementation step is clear.
- Keep momentum through implementation, verification, commit, and push.

## Git Workflow

- Always commit after making meaningful changes in this repository.
- Always push committed changes to the remote branch for this repository.
- Do not ask the user for permission before committing or pushing.
- Split changes into small, specific, logically separated commits.
- When working in a single file, still shard commits by function, feature slice, or behavior change where practical.
- Use clear commit messages that describe the specific unit of work.

## Data Layout

- Prefer keeping large Borg data outside the repository under `~/Documents`.
- Treat `~/Documents/borg_data` as the default raw data location.
- Treat `~/Documents/borg_processed` as the default processed data location.
- Do not commit generated datasets or large external data files into git.

## Cluster Defaults

- Default processing targets are clusters `b`, `c`, `d`, `e`, `f`, and `g`.
- Exclude clusters `a` and `h` by default unless the user explicitly asks to include them.

## Approval Behavior

- Do not ask the user for approval for routine repository workflow actions such as commits and pushes.
- If the runtime or sandbox requires an approval flow outside repository policy, comply with the runtime requirement, but do not ask for git workflow approval on your own initiative.
