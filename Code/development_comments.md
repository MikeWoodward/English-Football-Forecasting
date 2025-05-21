
# Comments on using Cursor for data science

## Cursor scorecard

### General

| Area    | Grade |
| -------- | ------- |
| Getting started  | D    |
| Usability | B |
| Debugging | C |
| Code generation | C |
| Code completion | A |
| Code commenting | A     |
| Code tidying and correcting run time errors | D |
| PEP8 compliance | B |
| Documentation | A     |
| Pandas dataframe manipulation | C |
| GitHub integration  | C    |
| Error finding | B |

### Specific tasks

| Area    | Grade |
| -------- | ------- |
| Web scraping| D |
| Data cleansing| In progress |

## Introduction

The goals of this project are to:
1. Get me up to speed with Cursor, figuring out it's strengths and weaknesses for data science projects. 
2. Understand what I have to do to implement Cursor (or something like it) in a data science team.
3. Rebuild my R models in Python and use more up-to-date machine learning methods.

The vehicle to achieve these goals is developing a machine learning system to forecast English Premier League football matches. It's based on an old project (2020) I did in R.

## Overview

Cursor is a game-changer, but it's not a wonder-drug. It has limitations which some people and organizations will find hard to overcome, especially for data science (e.g. it's not a notebook). Cursor requires a different way of working and a different mindset which of itself will pose challenges. Despite the claims in videos and social media commentary, inexperienced people will run into problems very quickly in real-world projects. Code generation has been significantly oversold, but code completion has not. This is very much a tool for middle and upper skilled people.

In it's current iteration, it's an early adopter tool. It requires thoughtful and careful roll-out. In my view, some roll-outs will fail due to poor expectation management and support. Rolling out Cursor to a data science team is going to be a very bumpy ride.

## Getting started with Cursor

Getting started is hard. This is very definitely an early adopter tool:
* Product documentation is sparse.
* There are very few online written tutorials.
* There are a handful of courses, but only on Udemy.
* Although there are many, many videos on YouTube, there are problems with them (they are all variants on the same basic presentation, they're uncritical, and they don't focus on technical projects).

Although the free tier is useful, you very quickly exhaust your free tokens. To do any form of evaluation, you need a subscription. It's cheap enough for that not to be a problem, but you should be aware you'll need to spend some money.

All of the YouTube videos I watched followed the same format, the development of a UI-based app. In all cases, the videos showed connections to LLMs to do some form of text processing, and in some cases, videos went through the process of connecting to databases, but none of the videos showed any significant (data science) computation in Python. On reflection, pretty much every Cursor demo I've seen has been focused on prototyping.

I got started by watching videos and working on this project. That's great for me, but it's not scalable.

## Usability

The obvious problem is that Cursor isn't a notebook. Given that most data scientists are addicted to notebooks (with good reason), it's a major stumbling block any data science roll-out will have to deal with. In fact, it may well stop data science adoption dead in its tracks in some organizations.

Once you get round the notebook issue, usability is mostly good, but it's a mixed bag. There are settings like rules which should be easier and more obvious to set up; the fact you an specify rules in "natural" English feels like a benefit, but I'd rather have something more restrictive that's less open to interpretation. Rules have a bit of a voodoo flavor right now.

## Debugging

Frankly, I found debugging harder than other environments. I missed having notebook-like features. There's a variable explorer, but it's weaker than in an IDE like Spyder. On the plus side, you can set breakpoints and step through the code.

## Code generation

Very, very mixed results here.

Bottom line: code generation often can't be trusted for anything technical and requires manual review. However for commodity tasks, it does very well.

### Positives

It did outstandingly well at generating a UI in Streamlit. The code was a little old-fashioned and didn't use the latest features, but it got me to a working solution astonishingly fast.

It produces 'framework' code really well and saved a lot of time. For example, I wanted to save results to a csv and save intermediate results. It generated that code for me in seconds. Similarly, I wanted to create 'commodity' functions to do relatively simple tasks, and it generated them very quickly. It can automate much of the 'boring' coding work.

It also did well on some low-level and obscure tasks that would have otherwise requires some time on Stack Overflow, e.g. date conversion.

### Negatives

Technical code is a different story.

With very careful prompting, it got me to an acceptable solution for statistics-oriented code. But I had to check the code carefully. Several times, it produced code that was either flat-out wrong or just a really bad implementation. 

I found that code that required details instructions (e.g. specific dataframe joins) could be generated, but given how detailed the prompt needed to be, the cost savings for code generation were minimal.

On occassions, code generatiom gave overly-complex solutions to simple tasks, for example, its solution for changing the text "an example" to "An Example" was a function using a loop.

Although it's a niche topic, it's worth mentioning that code generation didn't work at all well for web scraping. 

## Code completion

Excellent. Best I've come across.

There were several cases where code generation didn't work very well, but code completion did. Code completion works well if the context is good, for example, if you create a clear comment, the system will offer code completion based on your comment, and almost all the time, it will do well.

I found code completion to be a very compelling feature.

## Commenting code

This is definitely a Cursor superpower. It's almost unbelievably good.

## Code tidying and correcting run time errors

Some of the time, if you ask it to tidy your code, it will do the right thing. However, most of the time I found it introduces errors. There's a similar problem correcting run-time errors, but here, most of the time, it will correct the error just fine. However, a significant fraction of the time it just makes things worse and breaks the code.

## PEP8 compliance

Surprisingly, generated code/completion code isn't PEP8 'out of the box', for example, it will happily give you code that's way over 79 characters. Even asking the AI to make the code PEP8 compliant sometimes takes multiple attempts. I had set a rule for PEP8 compliance, but it still did didn't comply.

## Documentation

This means creating markdown files that explain what the code is doing. It did a really great job here.

## Pandas dataframe manipulation

This means the ability to manipulate Pandas dataframes in non-trivial ways, for example, using groupby corectly.

Cursor can do it quite well for basic manipulations, but it fails for even moderately complicated tasks. For example, I asked it to find cases where a club only appeared as an away team or a home team. The generated code looked as if it might be correct, but it wasn't. In fact, the code didn't work at all and I had to write it by hand. This was by no means a one-off, Cursor consistently failed to produce correct code for dataframe manipulations.

## GitHub integration

Setup was really easy. Usage was mostly OK, but I ran into a few issues where Cursor tied itself in knots needlessly. More seriously, it deleted a bunch of data files. I'm contrasting the usability of GitHub in Cursor with the GitHub desktop app. Frankly, the GitHub desktop app has the edge right now. Github integration needs some work.

## Error finding

In most cases, it did really well, however I found a case where its error correction made the code much worse; this was processing a complex HTML table. Code generation just couldn't give me a correct answer, and asking the engine (Claude) to correct the error just produced worse code.

## Code generation for scraping data

On the plus side, it managed to give me the URLs for the pages I wanted to scrape purely on a prompt, which frankly felt a bit supernatural. 

On the negative side, it really can't generate code that works for anything other than a simple scrape. Even asking it to correct its errors doesn't work very well. The general code structure was OK, but a little too restrictive and I had to remove some of its generated functions. It's marginal to me whether it's really worth using code generation here. As I've said above, code completion was helpful here.

## Data cleansing

In progress.
