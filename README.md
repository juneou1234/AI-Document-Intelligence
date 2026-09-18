# AI Document Intelligence

AI Document Intelligence is a Retrieval-Augmented Generation (RAG) application that allows a user to upload one PDF and ask questions about its contents.

The application extracts the document structure, creates semantic retrieval units, generates embeddings, retrieves relevant evidence, and uses Gemini to generate a grounded answer.

The system is designed to answer using information from the uploaded document rather than relying on outside knowledge.

---

## Features

- Upload one PDF at a time
- Extract text and document structure
- Build semantic document units
- Generate document embeddings
- Hybrid retrieval using semantic and lexical signals
- Query decomposition for complex questions
- Grounded answers using Google Gemini
- Source display for retrieved evidence
- Persistent document indexes
- Docker support
- Docker Compose support
- Handles unsupported questions without inventing information

---

## Architecture

The application follows this general pipeline:

```text
PDF
 |
 v
Document Extraction
 |
 v
Document Structure Detection
 |
 v
Semantic Chunking
 |
 v
Embeddings
 |
 v
Persistent Index
 |
 v
User Question
 |
 v
Query Decomposition
 |
 v
Hybrid Retrieval
 |
 v
Context Building
 |
 v
Gemini
 |
 v
Grounded Answer + Sources