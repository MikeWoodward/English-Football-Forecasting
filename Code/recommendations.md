WORK IN PROGRESS

# Recommendations for rolling out generative AI to data science and technical coding teams

## Summary - proceed with caution

There are substantial productivity gains to be had from rolling out generative AI for code generation to data science teams, but there are major issues to be managed and overcome. Without effective leadership, including expectation setting, roll-outs will fail. 

Replacing notebooks with an agentic AI like Cursor will not succeed. The most successful strategy is likely the combined use of notebooks and an agentic AI IDE to give data scientists an understanding of the benefits of the technology and its limitations. This is in preparation for the probable appearance of an agentic notebook product in the near future.

For groups that use IDEs (like software developers), I recommend immediate use of Cursor or one of its competitors.

## Introduction

### Why, who, and how

This is a guide for rolling out generative AI (meaning code generation) for data science teams. It covers the benefits you might expect to see, the issues you'll encounter, and some suggestions for coping with them. 

My comments and recommendations are based on my use of Cursor (an agentic IDE) along with Claude, Open AI and other code generation LLMs. I'm using them on multiple data science projects. 

As of June 2025, there are no data science agentic AI notebooks on the market, however, in my opinion, that's likely to change later on in 2025. Data science teams that understand the use of agentic AI for code generation will have an advantage over teams that do not, so early adoption is important.

Although I'm focused on data science, all my comments apply to anyone doing technical coding, by which I mean code that's algorithmically complex or uses "advanced" statistics. This can include people with the job titles "Analyst" or "Software Engineer".

I'm aware that not everyone knows what Cursor and the other agentic AI-enabled IDEs are, so I've added a section at the end of this document to explain what they are and what they do.

### The situation for software engineers

For more traditional software engineering roles, agentic AI IDEs offer substantial advantages and don't suffer from the "not a notebook" problem. Despite some of the limitations and drawbacks of code generation, the gains are such that I recommend an immediate managed, and thoughtful roll-out. A managed and thoughtful roll-out means setting realistic goals, having proper training, and clear communications. Realistic goals covers productivity gains; promising productivity gains of 100% or more is unrealistic. Proper training means educating the team on when to use code gen and when not to use it. Clear communications means the team must be able to share their experiences and learn from one another.

I have written separate notes for software engineering deployment.

## Benefits for data science

Cursor can automate a lot of the "boring" stuff that consumes data scientist's time, but isn't core algorithm development (the main thing they're paid to do). Here's a list:

* Commenting code. This includes function commenting using, for example, the Google function documentation format.
* Documentation. This means documenting how code works and how it's structured, e.g. create a markdown file explaining how the code base works.
* Boilerplate code. This includes code like reading in data from a data source.
* Test harnesses, test code, and test data. Code generation is excellent at generating regression test frameworks, including test data.
* PEP8 compliance. Cursor can restructure code to meet PEP8 requirements.

There are other key advantages too:

* Code completion. Given a comment or a specifc prompts, Cursor can generate code blocks, including using the correct API parameters. This means less time looking up how to use APIs.
* Code generation. Cursor can generate the outline of functions and much of the functionality, *but this has to be well-managed*.

Overall, if used corectly, Cursor can give a *significant* productivity boost for data science teams.

## Problems for data science

It's not plain sailing, there are several issue to overcome to get these productivity benefits.

### It's not a notebook

On the whole, data scientists don't use IDEs, they use notebooks. Cursor, and all the other agentic IDEs, are **not** notebooks. This is **the** most important issue to deal with and it's probably going to be the biggest cause of roll-out failure.

Notebooks have features that IDEs don't, specifically the ability to do "data interactive" development and debugging; this is the key reason why data scientists use them. Unfortunately, none of the agentic AI systems have anything that comes close to their power and there are no agentic AI notebooks that have gained widespread usage. 

Getting data scientists to abandon notebooks and move wholesale to an agentic IDE like Cursor is an uphill task and is unlikely to succeed. 

### A realistic view of code generation for data science

Cursor and LLMs in general, are bad at generating technically complex code, e.g. code using "advanced statistical" methods. For example, asking for code to demonstrate random variable convolution can sometimes yield weird and wrong answers. The correctness of the solution depends *precisely* on the prompt. It also needs the data scientist to closely review the generated code. Given that you need to know the answer and you need to experiment to get the right prompt, the productivity gain of using code generation in these cases is very low or even negative.

It's also worth pointing out that for Python code generation, code gen works very poorly for Pandas dataframe manipulation beyond simple transformations.

Code completion is slightly different from code generation and suffers from fewer problems, but it can yield crazily wrong code.

### Trashing code

Sometimes, code needs to be refactored. This means changing variable names, removing unused code, structuring code better, etc. In my experience, asking Cursor to do this can introduce serious errors

### Rules

Cursor rules are "settings" that control how code is generated. These settings are written in English prose, e.g. "Use meaningful variable names. Do not use df as the name of a dataframe variable." Rules are sent to the agentic LLM to provide context. Unfortunately, rules often have the flavor of magic spells and sometimes seem to be ignored. 

The failure to understand and manage rules may be a reason why roll-outs fail.

## General comments

### Data scientists are not software engineers and neither is Cursor

Data scientists focus on building algorithms, not on complete systems. In my experience, data scientists are bad at structuring code (e.g. functional decomposition), a situation made worse by notebooks. Neither Cursor, nor any of its competitors or LLMs, will make up for this shortcoming. 

### "Accept all" will lead to failure

I'm aware of real-world cases where junior staff have blindly accepted all generated code and it hasn't ended well. Bear in mind, generated code can sometimes be very wrong. All generated code (and code completion code) *must* be reviewed. 

## Code generation pilot and roll-out recommendations

### Clear goals and measuring success

All projects need clear goals and some form of success metric. For code generation for data science, goals and metrics might be:

"To evaluate the productivity impact of using code generation for data science. This includes understanding the benefits, pitfalls, and best ways of working. The goal is to clearly recommend if/how code generation should be used and appropriate ways of working with it. Deliverables are 1) a written report including a list of recommendations, 2) a presentation to company executives."

A good staff metric might be to measure participants engagement in the Slack channel (or other forum). Everyone involved should be communicating frequently, clearly, and valuably. 

### Initial briefing and on-going communications - expectation setting

Everyone in the process must have a realistic sense of the benefits of this technology and the problems, this includes the staff doing the work, their managers, and all executive and C-level staff.

Here are my suggestions:
* Written briefing on benefits and problems.
* Briefing meetings for all stakeholders.
* Regular feedback sessions for hands-on participants. These sessons are where people share their experiences.
* Regular reports to executives on project progress.
* On-going communications forum. This could be something like a Slack channel.

### Clear lines of responsibility

Assuming there are multiple people involved in an evaluation or roll-out, we need to define who does what. For this project, this means:
* One person to act as the rules controller. The quality of generated code depends on rules, if everyone uses wildly differen rules the results will inconsistent. The rules controller will provide recommended rules that everyone should use. Participants can experiment with rules, but they must keep the controller informed.
* One person to act as recommendations controller. As I've explained, there are "dos" and "don'ts" for working with code generation. One person should be responsible for continually keeping this up to date. 

### Limits on ways of working and project scope

There are multiple IDEs on the market and their are multiple LLMs that will generate code. Evaluating all of them will take considerable time and be expensive. My recommendation is to choose one IDE (e.g. Cursor, Windsurf, Lovable or one of the others) and one agentic AI. It's OK to have some experimentation at the boundaries, e.g. experimenting with a different agentic AIs, but this needs to be managed - as always, project discipline is important.

### Training

Just setting people up and telling them to get started won't work. You need to train the team how to use agentic IDEs like Cursor. You should record the training so everyone can access it later if they run into trouble. Training must include what not to do, including pointing out failure modes (e.g. blingly accepting generated code).

It may also be worth re-training people partway through the project with the knowledge gained so far.

### Notebook and Cursor roll-out

This is the core problem for data science. Figuring out a way of using an agentic IDE and a notebook together will be challenging. Here are my recommendations.

1. Find a way of ensuring the agentic IDE and the notebook can use the same code file. 

### Rules

### Regression tests

## What is Cursor - agentic AI IDE

