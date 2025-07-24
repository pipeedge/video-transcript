You are a professonal developer, your tasks is to build the similar app with MFM with the core functions as follows (use open-sourced LLM first if the instruction provided LLM is not open-sourced)

### **Project Brief: AI-Powered Podcast Analysis and Insight Extraction Application**

**Backgroud** MFM Vault.com (https://www.youtube.com/watch?v=NQtWHOUmqNw&ab_channel=GregKamradt) designed to extract insights, frameworks, and stories from a large podcast series. 

**Objective:** To construct an application that processes a podcast series from YouTube, extracts actionable insights, and provides a rich, searchable interface for users. This guide will walk you through the core development phases, with a focus on leveraging a Large Language Model (LLM) for the heavy lifting of content transformation and analysis.

**Guiding Principle:** We will follow the architecture of MFM Vault, using a combination of specialized tools for tasks like downloading and transcription, and a powerful LLM for the nuanced work of text enhancement, summarization, and insight extraction. While the following prompts are designed to be effective with many models, they can be adapted for your preferred open-source LLM.

You are a professonal developer, your tasks is to build the similar app with MFM with the core functions following the steps below(use open-sourced LLM first if the instruction provided LLM is not open-sourced).

---

### **Phase 1: Data Ingestion and Transcription**

Before the LLM can work its magic, we need to acquire and transcribe the podcast audio.

1.  **Video and Audio Acquisition:**
    * **Tooling:** Use `pytube` to fetch the list of all video episodes from the target YouTube channel.
    * **Action:** For each video, use the `yt-dlp` library to download the content and extract the audio into a high-quality format (e.g., MP3 or FLAC).

2.  **Audio Transcription:**
    * **Tooling:** Utilize a transcription service like **Deepgram** (specifically, the Nova 2 model is recommended for its accuracy). Alternatives include AssemblyAI or Google's transcription services.
    * **Configuration:** When submitting the audio for transcription, ensure you enable **diarization** (to distinguish between different speakers) and **punctuation**. The output will be a raw transcript, likely with timestamps for each word or phrase, but potentially lacking polished formatting. This raw, timestamped text is the input for our next phase.

---

### **Phase 2: The LLM Core – Content Processing and Enrichment**

This is where the LLM performs the most critical tasks. We will "hydrate" the raw transcript to make it valuable and user-friendly.

#### **Task 1: Segment Hydration – Cleaning Text for Display**

The initial transcript is functional but not readable. Your first task is to clean it up.

* **LLM Prompt for Text Formatting:**
    > "You are an expert in text formatting and linguistics. The following text is a raw, machine-generated transcript of a podcast segment. It may lack proper capitalization, punctuation, and sentence structure. Your task is to process this text and transform it into a clean, readable, and well-formatted paragraph. Ensure that you correct capitalization, add appropriate punctuation (periods, commas, question marks), and structure the text for maximum readability. Do not alter the underlying words or meaning. Here is the raw text:"
    >
    > `[Insert raw transcript segment here]`

#### **Task 2: Segment Hydration – Generating Segment Titles**

To help users navigate the content, each logical segment of the conversation needs a title.

* **LLM Prompt for Title Generation:**
    > "You are a skilled content editor. I will provide you with a segment of a podcast transcript. Based on the content of this segment, generate a concise and descriptive title, no more than 7-10 words long. The title should capture the main topic or idea being discussed. If you were to give a title to this segment, what would it be? Here is the segment:"
    >
    > `[Insert cleaned transcript segment here]`

#### **Task 3: Core Insight Extraction**

This is the heart of the application. We will extract structured insights from the entire episode.

* **Meta-Prompting for Category Definition (A Preparatory Step):**
    Before you begin extracting, you need to define the categories of insights. Instead of hardcoding them, use an LLM to help you brainstorm.
    * **LLM Prompt for Category Discovery:**
        > "I am building a tool to extract key insights from business and entrepreneurship podcasts. Based on your knowledge of this domain, what are the most valuable and logical categories of information I should extract from a podcast transcript? I'm thinking of things like business ideas, mental models, and interesting stories. What categories do you think I should extract from this podcast to provide the most value to users?"

    * **Action:** Use the LLM's response (e.g., "Frameworks," "Stories," "Products Mentioned," "Actionable Advice," "Quotes") and apply your own "human flavor" to finalize your extraction schema.

* **The Main Extraction Process (with a Crucial Tip):**
    To avoid exceeding the LLM's context window limit, do not feed the entire transcript at once.
    1.  **Chunking:** Programmatically divide the full episode transcript into smaller, overlapping chunks.
    2.  **Iterative Extraction:** Run the following prompt on *each individual chunk*.
    3.  **Deduplication:** After processing all chunks, perform a deduplication exercise to merge identical or highly similar insights that were extracted from the overlapping portions of the chunks.

    * **LLM Prompt for Insight Extraction (per chunk):**
        > "Please carefully read the following podcast transcript chunk. Your task is to extract all the key insights discussed. Organize these insights into the following categories: [Insert your finalized categories here, e.g., Frameworks, Stories, Products, Quotes]. For each insight, provide the verbatim quote or a detailed summary of the concept. Here is the transcript chunk:"
        >
        > `[Insert transcript chunk here]`

#### **Task 4: Timestamp Extraction for Deep-Linking**

To allow users to jump directly to the moment an insight was mentioned, you need to find its precise start and end time in the video.

* **LLM Prompt for Timestamp Identification:**
    > "I will provide you with a full podcast transcript that includes timestamps, and a specific quote or insight that was extracted from it. Your task is to find the exact start and end time of when this specific quote or insight was said in the podcast. Analyze the transcript and return only the start and end times in seconds. Here is the transcript:"
    >
    > `[Insert the full, original, timestamped transcript here]`
    >
    > "And here is the quote/insight you need to find:"
    >
    > `[Insert the specific extracted quote or insight here]`

---

### **Phase 3: Search, Retrieval, and Advanced Features**

With the content processed and enriched, the final steps involve making it accessible and adding value.

* **Fast Search Index:**
    * **Tooling:** Use **MeiliSearch** to index all the cleaned segments, titles, and extracted insights.
    * **Functionality:** This will enable users to perform lightning-fast searches and filter results by episode, speaker, or category.

* **External Product Information:**
    * **Tooling:** When an insight in the "Products" category is identified, use APIs from services like **Perplexity** or **Exa** to perform a web search.
    * **Action:** Use the product name to find its official website, description, and other relevant details, which you can then display in your app.

* **Related Insights (Semantic Similarity):**
    * **This is a database task, not an LLM prompt task.**
    * **Tooling:** Use a vector database like **Postgres with the `pg_vector` extension** (as used in Supabase).
    * **Process:**
        1.  For each extracted insight, use a sentence-transformer model to generate a numerical vector embedding.
        2.  Store these embeddings alongside the insights in your database.
        3.  Create a custom SQL function (e.g., `find_similar_insight`) that takes an insight's embedding as input and uses a distance metric (like cosine similarity) to find and return the most semantically similar insights from the entire database.

By following this structured approach, you can systematically build a powerful application that transforms unstructured podcast conversations into a structured, searchable, and highly valuable knowledge base.