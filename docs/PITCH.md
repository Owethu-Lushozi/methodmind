# Idea pitch — MethodMind (Koa's Lab)

## One-line description

MethodMind is an autonomous multi-agent learning colleague that helps students transfer a problem-solving method from a worked example to a new problem.

## The problem

Students often understand one demonstrated solution but struggle when the same skill appears in a different-looking question.

## The solution

A diagnostic agent identifies the misconception; a teaching agent creates targeted learning material and a transfer exercise; a reviewer agent checks the mathematics, flags errors and triggers corrections; the system evaluates the student's new attempt.

## Why it's autonomous

The planned orchestrator selects next steps from the learner's input and reviewer results, loops to correct failures, and gives a verified outcome or a transparent failure—not just a fixed answer script.

## MVP boundaries

Start with linear equations. Demonstrate one complete learning cycle. Use synthetic data. Store session state in memory rather than adding a database prematurely.

## 60–90 second speaking notes

Hi everyone, I'm Owethu Lushozi, representing Koa's Lab as a solo developer. My idea is MethodMind, an autonomous AI learning colleague.

I've noticed that students often understand a worked example, but get stuck on another question that uses the same method. They can follow the answer without yet being able to apply the principle independently.

MethodMind is designed to close that gap. A diagnostic agent identifies where the learner is struggling; a teaching agent develops an explanation and a new practice problem; and a reviewer independently checks the mathematics and requests corrections when something is wrong.

The system then evaluates the learner's attempt at a different question to see whether they can transfer the method. For this hackathon, I'm starting with foundational algebra and focusing on a reliable, visible self-correction cycle.

My goal is an AI colleague that helps students become independent problem-solvers, not just recipients of answers. Thank you.
