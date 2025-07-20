# Developer Notes
# Meta Themes:
- Future commits should update this file with additional findings.
- Record any setup steps or meta preferences here for future contributions.  
- Refine the process based on repeated observations
    - In particular think in terms of level of abstraction, efficient informatation acquisition.   

# Style Guide:
- Write unit tests for new functions and integration tests when suitable.
- Keep comments brief and prefer using high level libraries (`pandas`, `numpy`, `enum`).
- Avoid passing data via raw strings if structured types fit better.
- Follow DRY and prefer clear abstractions.
- Use appropriate abstractions.
- Safety scoring now uses weighted crime types and population density.

# Info
- Install dependencies with `pip install -r requirements.txt` before running tests.
- Run tests via `pytest -q`.
- The project TODO list is in `spec/TODO.md`. Update it when tasks are completed. 
- In general tasks should be addressed by the process:

# Process Loop
- View the TODO list
- Reviewing the associated code
- Thinking hard about the next steps given the context of the overall project.
- Breaking the task up into smaller tasks. 
- Writing those subtasks down in the TODO list. 
- Implementing those subtasks. 
- Writing unit tests for those subtasks. 
- Marking the task and subtasks as done or in need of further refinement.
- Updating any of the appropriate readmes in spec/ updating 
- Write down decisions containing context information for future LLM agent's work. 
- Write context to # LLM Sandbox as desired

# Meta Loop
- Review the current request
- Add the request to the previous user requests loop
- Examine the loops for similarities with other requests and with user requests summaries
- Increment the User Request Components and remove the associated portion of the request.

# LLM Sandbox
...

# User Request Components
...

# Previous User Requests
- Added request to continue TODO implementation and execute process/meta loops (2025-07-20)
- Completed Phase 3 and Phase 4 tasks (2025-07-21)