# Reply templates & edge cases

## Reply templates

**Fix reply (default):**

````markdown
Fixed in {NEW_SHA_SHORT}. {IMPLEMENTATION_NOTE}

See [{FILE}:{LINE}](https://github.com/{OWNER}/{REPO}/blob/{NEW_SHA}/{FILE}#L{LINE}).
````

- `{NEW_SHA_SHORT}` is the first 7 characters of the SHA
- `{IMPLEMENTATION_NOTE}` is a 1-2 sentence summary of what the fix does, based on the implementer's report
- Include a link to the specific line in the new commit so the reviewer can jump straight to the fix

Before posting each Fix reply, offer customization:

```
Reply preview:
  {PREVIEW}

(P)ost as-is / (C)ustomize / (S)kip reply?
```

- **Customize:** let the user rewrite the reply text (keeping the SHA link at the bottom)
- **Skip reply:** still resolves the thread but doesn't post anything

**Push back reply:**

````markdown
{USER_REASONING}
````

- Use the user's text verbatim. No skill-authored preamble.

**Defer reply:**

````markdown
⏸️ Deferred: {USER_REASON}
````

## Edge cases

1. **PR has uncommitted changes on the working tree before you start.** Step 3 handles this — stash or abort.

2. **Push fails (rebased, conflict).** Surface the error, show `git status`, ask the user how to proceed. Do not force-push.

3. **Type check fails after fix.** Show errors, ask: (1) re-dispatch implementer with error context, (2) abort all fixes and revert, (3) proceed anyway (strongly discouraged).

4. **Thread has multiple comments already (chain of replies).** The skill still posts a new reply to the chain using `in_reply_to` on the original comment. Do not try to reply to nested replies — GitHub's API threads all replies off the original comment.

5. **Comment body is empty or unparseable.** Default severity to ⚪, use "Review comment" as the title, show the raw body in the walkthrough.

6. **Multi-package monorepo with multiple tsconfigs.** The auto-detected type check command might not cover all packages. If the implementer touches files outside the default tsconfig scope, run `turbo run check-types` or equivalent if available.

7. **Branch checkout in Step 3 fails because of conflicts.** Abort and let the user resolve manually.
