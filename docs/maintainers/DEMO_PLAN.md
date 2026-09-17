# 30–60 second demo plan

## Goal

Show continuity and controlled state handling, not implementation terminology.

1. Open a fresh AI session with no chat history.
2. Give it a small Project Corpus folder and ask it to load the project.
3. Let it state the project ID, lifecycle status, active Task, and exact next
   action from canonical state.
4. In a provisioned local Runtime demo, make one controlled STATUS update with
   an expected hash and show the resulting audit receipt.
5. Start a second fresh AI session.
6. Show that it reloads the updated canonical state and continues from the new
   exact next action.

Use an invented, non-sensitive project. Say explicitly that manual mode does
not enforce Runtime controls and that Runtime guarantees are scoped to its
qualified local modes.
