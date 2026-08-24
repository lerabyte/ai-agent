# Glossary

## Agent

A program in which a model can choose an action, receive the result, and decide what to do next.

## Language model

The component that reads the conversation and produces either a final answer or a structured tool request.

## Message

One item in the conversation. A message includes a `role` and its content.

## Role

The sender of a message, such as `user`, `assistant`, or `tool`.

## Tool

A normal Python function that the model is allowed to request. Python decides whether and how the function runs.

## Tool schema

The JSON description that tells the model a tool's name, purpose, and parameters.

## Tool call

The structured request returned by the model when it wants Python to run a tool.

## Tool result

The message Python sends back after running the requested function.

## Agent loop

The repeated cycle of calling the model, running requested tools, returning results, and stopping at a final answer.

## Dispatch

Matching a requested tool name to the Python function that implements it.

## Approval

A user decision required before a higher-impact action runs.

## Sandbox

A boundary that restricts an action to an allowed location or set of resources.

## Step limit

The maximum number of model turns allowed before the program stops the loop.

