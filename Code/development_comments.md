# Comments on the process

## Cursor scorecard

| Area    | Grade |
| -------- | ------- |
| Getting started  | D    |
| Usability | B |
| Debugging | C |
| Code completion | A |
| Code commenting | A     |
| GitHub integration  | A    |
| Error finding | B |
| Code generation for web scraping | D |
| Data cleansing| In progress |

## Introduction

The overall goal of this project is to build a machine learning system to forecast English Premier League football matches. It's based on an old project (2020) I did in R.

I had several goals:
1. Get me up to speed with Cursor, figuring out it's strengths and weaknesses for data science projects.
2. Rebuild my R models in Python and use more up-to-date machine learning methods.

## Overview

Cursor is a game-changer, but it's not a wonder-drug. It has limitations which some people and organizations will find hard to overcome. It requires a different way of working and a different mindset. Despite the videos and social media commentary, inexperienced people will run into problems very quickly in real-world projects. This is a tool for middle and upper skilled people.

In it's current iteration, it's very much an early adopter tool. 

## General observations

For Cursor to work:
* You must have a good internet connection
* Cursor's servers must be up and running.
* You very quickly exhaust the free tier. To do anything useful, you need to subscribe.

This means code development has now become SaaS.

You should "reset" the chat between code generation tasks for different files. If you don't, code generation requests take longer and longer.

There's no notebook option, this is a classic coding IDE, which is unsurprising because it's based on VSCode.

## Getting started with Cursor

Getting started is hard. This is very definitely an early adopter tool:
* Product documentation is sparse.
* There are very few written tutorials online.
* There are a handful of courses, but only on Udemy.
* Although there are many, many videos on YouTube, there are problems with them (they are all variants on the same basic presentation, they're uncritical, and they don't focus on more technical problems).

All of the YouTube videos I watched followed the same format, the development of a UI-based app. In all cases, the videos showed connections to LLMs to do some form of text processing, and in some cases videos went through connecting to databases, but none showed any significant (data science) computation in Python. None of the videos I could find were aimed at 'traditional' data science or analytics. On reflection, all of the vidoes had the flavor of a good sales engineer presentation.

I got started by watching videos and working on this project. That's great for me, but it's not scalable.

## Usability

Mostly good, but a mixed bag. I'm not familar with VS Code (Cursor is built on VS Code), which made things a little harder (I'm not knocking it for this). There are things like rules which should be easier and more obvious to set up. The fact you an specify rules in "natural" English feels like a benefit, but I'd rather have something more restrictive that's less open to interpretation, may be a combination would work well.

## Debugging

Frankly, I found debugging harder than other environments. I missed having notebook-like features. There's a variable explorer, but it's weaker than in an IDE like Spyder. On the plus side, you can set breakpoints and step through the code.

## Code completion

Excellent. Best I've come across.

## Commenting code

This is definately a Cursor superpower. It's almost unbelieveably good.

## GitHub integration

Outstanding.

## Error finding

In most cases, it did really well, however I found a case where its error correction made the code much worse; this was processing a complex HTML table. Code generation just couldn't give me a correct answer, and asking the engine (Claude) to correct the error just produced worse code.

## Code generation for scraping data

On the plus side, it managed to give me the URLs for the pages I wanted to scrape purely on a prompt, which frankly felt a bit supernatural. 

On the negative side, it really can't generate code that works for anything other than a simple scrape. Even asking it to correct its errors doesn't work very well. The general code structure was OK, but a little too restictive and I had to remove some of its generated functions. It's marginal to me whether it's really worth using code generation here.

Code completion was very useful here.

## Data cleansing

This data set is a very difficult one to cleanse automatically. There are several oddities, for example:
* How to cope with "phoenix clubs". These are clubs that went bankrupt and then were revived. The rules are the team has to have a different name. In practice, teams that have gone bankrupt and then were revived take on a new name and a few years later petition for the old name back.
* How to cope with Wimbledon. Wimbledon moved to to Milton Keynes in 2004 and changed their name to "Milton Keynes Dons". Fans in Wimbledon formed a new local team called "AFC Wimbledon". Both "Milton Keynes Dons" and "AFC Wimbledon" have played in the same league and played each other.
* Nicknames, abbreviations, and truncations. Manchester United is sometimes known as MUFC, Man United, Man Utd, and various variants.
* The league names have changed over the years.

I did this data cleansing by hand, it's far too tricky to do otherwise.
