# Developer Notes
# Info
- You don't have access to text editors e.g. vim, nano.
- Run tests via `pytest -q`.
- The project TODO list is in `README.md`. Update it when tasks are completed.
- Tasks should be addressed by following the process loop:
- Create/update the AGENTS.md within each directory to document the directory's purpose, tasks, and any relevant information for future developers.

# Style Guide:
- Write unit tests for new functions and integration tests when suitable.
- Keep comments brief and prefer using high level libraries (`pandas`, `numpy`, `enum`).
- Avoid passing data via raw strings if structured types fit better.
- Follow DRY and prefer clear abstractions.
- Use appropriate abstractions.
- Run `black` on your code before committing. Otherwise, avoid working on formatting.

# Process Loop
- View the TODO list
- Review the associated code
- Think hard about the next steps given the context of the overall project.
- Break the task up into smaller tasks. 
- Writ those subtasks down in the TODO list. 
- Implement those subtasks. 
- Write unit tests for those subtasks. 
- Mark the task and subtasks as done or in need of further refinement.
- Update the README.md document
 