WORK IN PROGRESS

# Recommendations for rolling out generative AI to data science and technical teams

## Summary - proceed with caution

There are substantial productivity gains to be had from rolling out generative AI for code generation to data science teams, but there are major issues to be managed and overcome. Without effective leadership, including expectation setting, roll-outs will fail. 

Replacing notebooks with an agentic AI like Cursor will not succeed. The most successful strategy is likely the combined use of notebooks and an agentic AI IDE to give data scientists an understanding of the benefits of the technology and its limitations. This is in preparation for the likely appearance of an agentic notebook product.

For groups that use IDEs, I recommend immediate use of Cursor or one of its competitors.

## Introduction

### Why, who, and how

This is a guide for rolling out generative AI, meaning code generation, for data science teams. It covers the benefits you might expect to see, the issues you'll encounter, and some suggestions for coping with them. 

My comments and recommendations are based on my use of Cursor (an agentic IDE) along with Claude, Open AI and other code generation LLMs. I'm using them on multiple data science projects. 

As of June 2025, there are no data science agentic AI notebooks on the market, however, in my opinion, that's likely to change later on in 2025. Data science teams that understand the use of agentic AI for code generation will have an advantage over teams that do not.

Although I'm focused on data science, all my comments apply to anyone doing technical coding, by which I mean code that's algorithmically complex or uses "advanced" statistics. This can include people with the job titles "Analyst" or "Software Engineer".

I'm aware that not everyone knows what Cursor and the other agentic AI-enabled IDEs are, so I've added a section at the end of this document to explain what they are and what they do.

### The situation for software engineers

For more traditional software engineering roles, agentic AI IDEs offer substantial advantages and don't suffer from the "not a notebook" problem. Despite some of the limitations and drawbacks of code generation, the gains are such that I recommend an immediate managed, and thoughtful roll-out. A managed and thoughtful roll-out means setting realistic goals, having proper training, and clear communications. Realistic goals covers productivity gains; promising productivity gains of 100% or more is unrealistic. Proper training means educating the team on when to use code gen and when not to use it. Clear communications means the team must be able to share their experiences and learn from one another.

## Benefits for data science

Cursor can automate a lot of the "boring" stuff that consumes data scientist's time, but isn't core algorithm development. Here's a list:

* Commenting code. This includes function commenting using, for example, the Google function documentaiton format.
* Documentation. This means documenting how code works and how it's structured.
* Boilerplate code. This includes code like reading in data from a data source.
* PEP8 compliance. It can restructure code to meet PEP8 requirements.

There are other key advantages:

* Code completion. Given a comment or a specifc prompts, Cursor can generate code blocks, including using the correct API parameters. This means less time looking up how to use APIs.
* Code generation. Cursor can generate the outline of functions and much of the functionality, but this has to be well-managed.

Overall, if used corectly, Cursor can give a *significant* productivity boost for data science teams.

## Problems for data science

It's not plain sailing, there are several issue to overcome to get the productivity benefits.

### It's not a notebook

On the whole, data scientists don't use IDEs, they use notebooks. Cursor, and all the other agentic IDEs, are not notebooks. This is **the** most important issue to deal with and it's probably going to be the biggest cause of roll-out failure.

Notebooks have features that IDEs don't, specifically the ability to do "data interactive" development and debugging; this is the key reason why data scientists use notebooks. Unfortunately, none of the agentic AI systems have anything that comes close to the power of notebooks and there are no agentic AI notebooks that have gained widespread usage. 

Getting data scientists to abandon notebooks and move wholesale to an agentic IDE like Cursor is an uphill task and is unlikely to succeed. 

### A realistic vew of code generation for data science



### Data scientists are not software engineers and neither is Cursor

## Roll out recommendations

## What is Cursor - agentic AI IDE

