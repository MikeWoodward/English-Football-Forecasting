# Comments on the process

## Cursor scorecard

| Area    | Grade |
| -------- | ------- |
| Getting started  | D    |
| Usability | B |
| Debugging | C |
| Code commenting | A     |
| GitHub integration  | A    |
| Error finding | B |
| Code generation for web scraping | D |

## Introduction

I had several goals with this project:
1. Get me up to speed with Cursor, figuring out it's strengths and weaknesses for data science projects.
2. Rebuild my R models in Python.

## Getting started with Cursor

Getting started is hard. This is very definately an early adopter tool:
* Product documentation is sparse.
* There are very few written tutorials online.
* There are a handful of courses, but only on Udemy.
* Although there are many, many videos on YouTube, there are problems with them.

All of the YouTube videos I watched followed the same format; the development of a UI-based app. In all cases, the videos showed connections to LLMs to do some form of text processing, and in some cases videos went through connecting to databases, but none showed any significant computation in Python. None of the videos I could find were aimed at 'traditional' data science or analytics.

I got started by watching videos and working on this project. That's great for me, but it's not scalable.

## Usability

Mostly good, but a mixed bag. I'm not familar with VS Code (Cursor is built on VS Code), which made things a little harder (I'm not knocking it for this). There are things like rules which should be easier and more obvious to set up. 

## Debugging

Frankly, I found debugging possible, but much harder than other envionments. I missed having notebook-like features. There's no variable explorer. You can't easily comment out blocks of code. 

## Commenting code

This is definately a Cursor superpower. It's almost unbelieveably good.

## GitHub integration

Outstanding.

## Error finding

In most cases, it did really well, however I found a cases where its error correction made the code much worse. This was processing a complex HTML table. Code generation just couldn't give me a correct answer, and asking the engine (Claude) to correct the error just produced worse code.

## Code generation for scraping data

It really can't generate code that works for anything other than a simple scrape. Even asking it to correct its errors doesn't work very well. The general code structure was OK, but a little too restictive and I had to remove some of its generated functions. It's marginal to me whether it's really worth using code generation here.

