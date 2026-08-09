#ANY LANGUAGE TO ENGLISH TRANSLATION PROMPT
LANGUAGE_TRANSLATION_PROMPT = """
        You are a professional translator.

        Translate the following {language} transcript into natural English.

        Rules:
        - Strictly translate to english language only.
        - Do NOT summarize.
        - Do NOT explain.
        - Preserve the meaning.
        - Preserve technical terms and programming keywords.
        - Return ONLY the translated transcript.

        Transcript:

        {transcript}
        """


TOPIC_EXTRACTOR_PROMPT = """
        You are an expert GATE Computer Science instructor.

        Read the following lecture transcript.

        Identify:

        1. The primary GATE CSE subject out of the folllwing list only 
                Engineering Mathematics
                Digital Logic
                Computer Organization & Architecture
                Programming & Data Structures
                Algorithms
                Theory of Computation
                Compiler Design
                Operating Systems
                Database Management Systems
                Computer Networks
                General Aptitude
        2. If the subject is not related to GATE compute science and engineering, return "Not related to GATE CSE" as the subject and an empty list of topics.
        3. The important topics discussed.
        4. Strictly give the topic name only, do not give any explanation or description
        5. IF there is anything content inside a bracket like (example, case study, etc.), ignore it and do not include it in the topic name.

        Return ONLY valid JSON.

        Example:

        {{
        "subject":"Operating Systems",
        "topics":[
                "Deadlock",
                "Necessary Conditions",
                "Deadlock Prevention"
        ]
        }}

        Transcript:

        {transcript}
        """


INTERNET_SEARCH_PROMPT = """Search the web.

        Find authentic GATE Previous Year Questions related to

        Subject:
        {subject}

        Topic:
        {topic}

        For each question provide

        - Year
        - Question

        Rules:
        - Give as many questions as possible 
        - Exactly quote the internet.
        - Do not add anything extra.


        Return JSON only.
        Example 

        {{
        "Subject":"Operating Systems",
        "Topics":"Deadlock",
        "Year":"2019",
        "Question":"Explain the necessary conditions for deadlock in operating systems."
        }}
        """