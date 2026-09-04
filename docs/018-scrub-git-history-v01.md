# Plan: Remove Sensitive File from Git History

## Objective

Permanently remove a sensitive file containing an API key from the entire Git history of the `set-psi-validation` repository.

## Background & Motivation

A file containing a sensitive GAS API key was accidentally committed to the repository. While the user is planning to rotate the key, the history must be scrubbed to ensure the secret is not accessible in previous commits.

## Scope & Impact

- This is a **destructive operation**.
- All commit hashes for affected commits will change.
- All remote repositories and clones will be desynchronized.
- Requires a force-push to the remote repository after completion.

## Implementation Steps

### 1. Preparation

- [ ] Create a full backup of the current repository state (e.g., zip the directory or `git clone --mirror`).
- [ ] Ensure all local changes are committed or stashed.
- [ ] Identify the exact file path to be removed.

### 2. Execution (Local Machine Recommended)

- [ ] The environment lacks `git-filter-repo`.
- [ ] **Action:** Perform the following on a machine where `git-filter-repo` is installed:

  ```bash
  # Ensure git-filter-repo is installed
  pip install git-filter-repo

  # Run the scrub operation
  git filter-repo --path <PATH_TO_SENSITIVE_FILE> --invert-paths
  ```

### 3. Verification & Cleanup

- [ ] Verify the file is removed from the current working directory and `git log`.
- [ ] Verify no other sensitive information was inadvertently exposed.
- [ ] Add the sensitive file or its directory to `.gitignore` to prevent re-committing.

### 4. Synchronization

- [ ] Perform a `git push --force` to the remote repository.
- [ ] Inform all collaborators that the repository history has been rewritten and they must re-clone or perform a hard reset.

## Migration & Rollback

- If the operation goes wrong, restore from the backup created in Step 1.
