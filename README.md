# SkillBridge

An AI Gap Analysis application that allow users to identify essential missing skills within a job posting, and find resources to learn from

![image](https://github.com/user-attachments/assets/c79abdb5-0b69-4ff0-894c-89a58f7dfd09)
![image](https://github.com/user-attachments/assets/b57df744-4f0e-4466-8514-0a18f30c4779)

## Why I build it

I want to effectively find resources to learn skills that I'm missing for a certain role. 

## Features
Semantic Skill Matching: Uses vector embeddings to match skills that are semantically similar even when terminology differs
Contextual Skill Weighting: Identifies and prioritizes required skills vs preferred skills in job descriptions
Personalized Learning Resources: Generates tailored recommendations for courses, books, and projects to develop missing skills
Multi-Agent Architecture: Leverages specialized AI agents for different parts of the analysis process

## Development is still on going

## Issues
-**Segmentation Fault with ChromaDB**: Memory issues when processing large vector operations
-**Application Startups takes some time**: We are initliazing an NER model that reads from a techinical skills database
-**Skills identification not complete**: Some skills are still being left out when comparing resume with job descriptions
-**Loading Speed**: Need to speed up agent communication 
