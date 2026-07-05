# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Owner -  represents the person using the app. It holds their ID, name, and preference dictionary, and keeps a list of Pets

Pets - represents the actual animal. Belongs to one Owner and keeps list of its Task objexts

Task - represents one care activity. It is a template for what the task is and not the schedule (holds name, duration, priority, and recurrence). 

Plan - represents a finished daily schedule for one per on a single day. Holds list of Task objects and has a method, explain, that returns a string describing the plan

**b. Design changes**

Based on AI feedback here are the changes that I made:

Owner - Added get_plans() so you can get from an Owner down to their schedules directly, instead of having to go through each Pet manually.

Pet - Made it so Pet also keeps a list of Plans because the UI needs to be able to show all of a Pet past plans without it you'd have no way to find plans from the pet side.

Task - Changed priority and recurrence from plain strings to enums so that values like "kinda important" get rejected instead of breaking scheduling logic.

PlanEntry (new) - represents one task as it appears in a specific plan, with a start time, end time, and completion status. Added because Plan was holding raw Task objects, which meant there was nowhere to record when something was scheduled or if it got done without modifying the original Task.

Plan - Holds a list of PlanEntry objects instead of raw Tasks, and has a new available_minutes attribute. Added the time budget here because the scheduler needs to know the constraint before filtering tasks, and the plan should remember it for when explain() describes why certain tasks were left out.

Scheduler (new) - the brain of the app. Takes a pet, a time budget, and a date, and creats the finished Plan. Added because nothing in the original four classes was actually responsible for building a schedule - would have ended up crammed into Plan making it messy and hard to test.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The filter_by_time method in pawpal_system.py decides which tasks make the plan when there isn't enough time for all of them. It takes in the tasks in priority order and keeps each one as long as it still fits in the remaining budget. It doesn't try to find the best possible combination of tasks to fill the time. It just takes them as they come. But this is reasonable for this sceanario because not only would a more "optimal" version be a lot more complex and likey slower to compute, this system actually makes the most sense realistically. You would want to do the more important tasks first!

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
AI was used to help verify and clean up my initial backend structure, implement core implementation, debug algorithms, answer questions I had, and write doclines and test cases for my methods.

**b. Judgment and verification**

One suggestion the AI made that I didn't implement was to update the owner name attribute explictily. I rejected this mostly because I thought it was unnecessary as it is unlikely the user would want to change their name.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
