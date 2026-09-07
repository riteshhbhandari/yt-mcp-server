from sqlalchemy import create_engine, text
from config import DATABASE_URL
import json

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(result.scalar())

# returns if the video ID exists or not
def get_video(video_id: str)-> int:
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    video_id
                FROM video
                WHERE video_id = :video_id
            """),
            {
                "video_id": video_id
            }
        )

        row = result.fetchone()

        if row is None:
            return 0

        return 1

def store_transcript(video_id: str, transcript: str, metadata: dict):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO transcript (video_id, transcipt)
                VALUES (:video_id, :transcript)
            """),
            {
                "video_id": video_id,
                "transcript": transcript
            }
        )
        connection.execute(
            text("""
                INSERT INTO video (video_id, video_title, channel_name, description)
                VALUES (:video_id, :video_title, :channel_name, :description)
            """),
            {
                "video_id": video_id,
                "video_title" : metadata.get("title"),
                "channel_name" : metadata.get("uploader"),
                "description" : metadata.get("description")
            }
        )
    print("Transcript stored successfully in table : transcript")

def get_transcript_from_db(video_id: str) -> str:
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                SELECT transcipt
                FROM transcript
                WHERE video_id = :video_id
            """),
            {"video_id": video_id}
        )
        row = result.fetchone()
        return row[0] if row else ""

#store the topics in database and link it to the subject ID
def store_topics(video_id: str, subject: str, topics: list):
    with engine.begin() as connection:
        result = connection.execute(
            text("""SELECT id FROM subjects WHERE subject_name = :subject_name"""),
            {"subject_name": subject}
            )
        subject_id = result.scalar()
        print ("subject_id", subject_id)

        
        for topic in topics:
            #store the topic in topic table with subject_id
            connection.execute(
                text("""
                    INSERT INTO topic (topic_name, subject_id)
                    VALUES (:topic_name, :subject_id)
                """),
                {
                    "topic_name": topic,
                    "subject_id": subject_id
                }
            )

            #extract topic_id for each topic.
            topic_id =connection.execute(
                text(""" select id from topic where topic_name = :topic_name"""),
                {"topic_name": topic}
                ).scalar()
            #scalar converts object into a single value
            #scalar returns the first column of the first row in the result set, or None if the result set is empty.
            print ("topic_id", topic_id)

            #store the video_id and topic_id in video_topic table
            connection.execute(
                text("""
                    INSERT INTO video_topic(video_id, topic_id)
                    VALUES (:video_id, :topic_id)
                """),
                {
                    "video_id": video_id,
                    "topic_id": topic_id
                }
            )
        print("Topic stored successfully in table : topic")

def get_topics(video_id: str) -> dict:
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                SELECT s.subject_name, t.topic_name
                FROM video_topic vt
                JOIN topic t ON vt.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE vt.video_id = :video_id
            """),
            {"video_id": video_id}
        )

        rows = result.fetchall()
        if not rows:
            return {"subject": "", "topics": []}

        #stores the subject name and topics in a dict
        subject_name = rows[0][0]
        topics = [row[1] for row in rows]
        
        # print("From database")
        # print("subject_name = ", subject_name, "topics = ", topics)

        #returns in form of dict
        return {"subject": subject_name, "topics": topics}

def store_questions(question_data: list):
    with engine.begin() as connection:
        for question in question_data:

          topic_result = connection.execute(
          text("""
              SELECT id
              FROM topic
              WHERE topic_name = :topic_name
              LIMIT 1
          """),
          {
              "topic_name": question.get("Topics")
          })

          topic_row = topic_result.fetchone()

          if not topic_row:
              raise ValueError(
                  f"Topic not found: {question.get('Topics')}"
              )

          topic_id = topic_row[0]
          # Normalize options
          options = question.get("Options")

          if isinstance(options, list):
              options = json.dumps(options)

          elif isinstance(options, str):
              # If it's already a JSON array
              try:
                  options = json.dumps(json.loads(options))
              except json.JSONDecodeError:
                  # Convert "A) ..., B) ..., C) ..., D) ..."
                  options = json.dumps([
                      option.strip()
                      for option in options.split(",")
        ])
          connection.execute(
                text("""
                    INSERT INTO questions (question_text, options, correct_answer, source, year, topic_id, difficulty)
                    VALUES (:question_text, :options, :correct_answer, :source, :gate_year, :topic_id, :difficulty)
                """),
                {
                    "question_text": question.get("Question"),
                    "options": options,
                    "correct_answer": question.get("Correct Answer"),
                    "source": question.get("Source URL"),
                    "gate_year": question.get("Year"),
                    "topic_id": topic_id,
                    "difficulty": question.get("Difficulty")
                }
            )
    print("Questions stored successfully in table : questions")

#dummy_data
def dummy_data():
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO video (video_id, video_title, channel_name, description)
                VALUES (:video_id, :video_title, :channel_name, :description)
            """),
            {
                "video_id": "dummy_video_id",
                "video_title" : "Dummy Video Title",
                "channel_name" : "Dummy Channel Name",
                "description" : "Dummy Description"
            }
        )

        result = connection.execute(
            text("""
                SELECT *
                FROM video
                WHERE video_id = :video_id
            """),
            {"video_id": "dummy_video_id"}
        )

        print(result.fetchone())
if __name__ == "__main__":
    test_connection()
    store_questions(
  [{
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Capacity and Addressing",
    "Year": "2023",
    "Difficulty": "Medium",
    "Question": "Consider a disk pack with 32 surfaces, 64 tracks and 512 sectors per track. 512 bytes of data are stored in a sector. The capacity of the disk pack and the number of bits required to specify a particular sector in the disk are respectively:",
    "Options": [
      "A. 512 MB, 20",
      "B. 1 GB, 20",
      "C. 512 MB, 19",
      "D. 1 GB, 19"
    ],
    "Correct Answer": "C",
    "Source URL": "https://gateoverflow.in/391118/gate-cse-2023-question-47"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "DRAM Refresh",
    "Year": "2021",
    "Difficulty": "Medium",
    "Question": "A DRAM chip, with 512 rows and 512 columns, has a refresh cycle of 4 ms. The time required for each refresh operation is 100 ns. What is the percentage of time spent on refreshing the DRAM?",
    "Options": [
      "A. 1.28%",
      "B. 0.0128%",
      "C. 12.8%",
      "D. 0.128%"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/357353/gate-cse-2021-set-1-question-27"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Access Time",
    "Year": "2020",
    "Difficulty": "Easy",
    "Question": "Consider a disk with 16384 cylinders, 16 surfaces, and 64 sectors per track. The cycle time of the disk is 8.33 ms. What is the maximum rotational delay?",
    "Options": [
      "A. 4.16 ms",
      "B. 8.33 ms",
      "C. 16.66 ms",
      "D. 2.08 ms"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/333148/gate-cse-2020-question-22"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "SRAM vs DRAM",
    "Year": "2019",
    "Difficulty": "Easy",
    "Question": "Which of the following is/are TRUE for SRAM and DRAM?",
    "Options": [
      "A. SRAM is faster than DRAM.",
      "B. DRAM is denser than SRAM.",
      "C. DRAM needs periodic refreshing.",
      "D. All of the above."
    ],
    "Correct Answer": "D",
    "Source URL": "https://gateoverflow.in/302830/gate-cse-2019-question-15"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Transfer Time",
    "Year": "2018",
    "Difficulty": "Hard",
    "Question": "A hard disk system has the following parameters: Number of tracks = 500, Number of sectors/track = 100, Number of bytes/sector = 500. If the disk rotates at 3000 rpm, and average seek time is 30 ms, what is the average time (in ms) to read a 500-byte sector from the disk?",
    "Options": [
      "A. 40.1 ms",
      "B. 30.1 ms",
      "C. 40.2 ms",
      "D. 41.0 ms"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/118318/gate-cse-2018-question-53"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "DRAM Refresh",
    "Year": "2017",
    "Difficulty": "Medium",
    "Question": "A DRAM has a refresh cycle of 128 ms. The number of rows in the DRAM is 2^14. The time taken to perform one refresh operation is 100 ns. The percentage of time the DRAM is unavailable for read/write operations is:",
    "Options": [
      "A. 1.28%",
      "B. 0.0128%",
      "C. 1.31%",
      "D. 0.128%"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/105658/gate-cse-2017-set-1-question-25"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Chip Select",
    "Year": "2016",
    "Difficulty": "Medium",
    "Question": "Consider a 16-bit processor which has a direct addressable memory capacity of 1024 KB. The size of the address bus is:",
    "Options": [
      "A. 10 bits",
      "B. 16 bits",
      "C. 20 bits",
      "D. 24 bits"
    ],
    "Correct Answer": "C",
    "Source URL": "https://gateoverflow.in/39561/gate-cse-2016-set-1-question-18"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Transfer Rate",
    "Year": "2015",
    "Difficulty": "Hard",
    "Question": "A disk has 200 tracks (numbered 0 to 199). At a given time, the disk arm is at track 100. The disk receives requests in the following order: 30, 85, 110, 100, 175. What is the total distance (in tracks) the disk arm moves to satisfy all requests using the Shortest Seek Time First (SSTF) algorithm?",
    "Options": [
      "A. 160",
      "B. 145",
      "C. 175",
      "D. 155"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/8215/gate-cse-2015-set-1-question-28"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Main Memory / Chip Select",
    "Year": "2014",
    "Difficulty": "Medium",
    "Question": "The amount of ROM needed to implement a 4-bit multiplier is:",
    "Options": [
      "A. 64 bits",
      "B. 128 bits",
      "C. 1024 bits",
      "D. 2048 bits"
    ],
    "Correct Answer": "D",
    "Source URL": "https://gateoverflow.in/1944/gate-cse-2014-set-2-question-19"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Constant Angular Velocity",
    "Year": "2013",
    "Difficulty": "Medium",
    "Question": "For a magnetic disk with 10 surfaces, 100 tracks per surface and 50 sectors per track, with 512 bytes per sector, what is the capacity of the disk in MB?",
    "Options": [
      "A. 25.6 MB",
      "B. 25.0 MB",
      "C. 51.2 MB",
      "D. 50.0 MB"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/2117/gate-cse-2013-question-13"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "RAM / Chip Select",
    "Year": "2011",
    "Difficulty": "Medium",
    "Question": "A computer has a 256 KB, 4-way set associative cache of 32-byte blocks. The main memory is 2^32 bytes. How many bits are there in the TAG field?",
    "Options": [
      "A. 20",
      "B. 21",
      "C. 11",
      "D. 16"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/2293/gate-cse-2011-question-33"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk CHS Addressing",
    "Year": "2009",
    "Difficulty": "Hard",
    "Question": "Consider a disk with the following specifications: 8 surfaces, 512 tracks/surface, 64 sectors/track, 1 KB/sector. The disk rotates at 3600 rpm. The average seek time is 8 ms. What is the average time to read a sector?",
    "Options": [
      "A. 16.59 ms",
      "B. 16.33 ms",
      "C. 13.33 ms",
      "D. 12.33 ms"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/908/gate-cse-2009-question-18"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Memory Hierarchy",
    "Year": "2008",
    "Difficulty": "Easy",
    "Question": "In a hierarchical memory system, the hit ratio of cache memory is 0.9. The access time for cache is 20 ns and main memory is 200 ns. What is the average access time?",
    "Options": [
      "A. 38 ns",
      "B. 40 ns",
      "C. 30 ns",
      "D. 22 ns"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/423/gate-it-2008-question-12"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "DRAM Refresh",
    "Year": "2007",
    "Difficulty": "Medium",
    "Question": "If the cycle time of a DRAM is 100 ns and the refresh period is 2 ms for 1024 rows, what percentage of memory cycles are used for refreshing?",
    "Options": [
      "A. 0.5%",
      "B. 5.12%",
      "C. 10.24%",
      "D. 1%"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/1063/gate-cse-2007-question-22"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "SRAM / DRAM",
    "Year": "2005",
    "Difficulty": "Easy",
    "Question": "Which of the following statements is false?",
    "Options": [
      "A. DRAM is used as main memory because it is cheaper and denser than SRAM.",
      "B. SRAM is used as cache memory because it is faster than DRAM.",
      "C. DRAM needs to be refreshed because its storage cell is a capacitor.",
      "D. SRAM is used as main memory because it is non-volatile."
    ],
    "Correct Answer": "D",
    "Source URL": "https://gateoverflow.in/1458/gate-cse-2005-question-16"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Capacity",
    "Year": "2004",
    "Difficulty": "Medium",
    "Question": "Consider a disk with 10 surfaces, 100 tracks per surface, and 50 sectors per track. Each sector can store 512 bytes. What is the total capacity of the disk?",
    "Options": [
      "A. 25 MB",
      "B. 256 MB",
      "C. 2.5 MB",
      "D. 25.6 MB"
    ],
    "Correct Answer": "D",
    "Source URL": "https://gateoverflow.in/1689/gate-cse-2004-question-28"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Rotational Latency",
    "Year": "2001",
    "Difficulty": "Easy",
    "Question": "The rotational latency of a disk with 5000 rpm is:",
    "Options": [
      "A. 6 ms",
      "B. 12 ms",
      "C. 5 ms",
      "D. 10 ms"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/656/gate-cse-2001-question-1-12"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Memory Hierarchy / Access Time",
    "Year": "2015",
    "Difficulty": "Medium",
    "Question": "A computer system has a L1 cache, L2 cache and main memory. The hit rates for L1 and L2 are 0.9 and 0.8 respectively. The access times are 1 ns, 10 ns and 100 ns respectively. What is the average memory access time?",
    "Options": [
      "A. 1.5 ns",
      "B. 3.0 ns",
      "C. 2.5 ns",
      "D. 4.0 ns"
    ],
    "Correct Answer": "B",
    "Source URL": "https://gateoverflow.in/8207/gate-cse-2015-set-1-question-23"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "DRAM Latency",
    "Year": "2014",
    "Difficulty": "Medium",
    "Question": "In a DRAM chip, the time taken to access data from a particular row is significantly higher than the time taken to access data from the same row if it is already open. This property is known as:",
    "Options": [
      "A. Page mode access",
      "B. Burst mode access",
      "C. Interleaved access",
      "D. Row address strobe"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/1941/gate-cse-2014-set-2-question-16"
  },
  {
    "Subject": "Computer Organization & Architecture",
    "Topic": "Disk Transfer Rate",
    "Year": "2010",
    "Difficulty": "Medium",
    "Question": "The transfer rate of a magnetic disk is 10 MB/s. The disk rotates at 6000 rpm. The capacity of each track is:",
    "Options": [
      "A. 100 KB",
      "B. 1 MB",
      "C. 10 KB",
      "D. 600 KB"
    ],
    "Correct Answer": "A",
    "Source URL": "https://gateoverflow.in/2361/gate-cse-2010-question-26"
  }])
    # store_topics("xyz1",{'subject': 'Computer Organization & Architecture', 'topics': ['Magnetic Disk', 'Platters', 'Spindle', 'Read-Write Head', 'Arm Assembly', 'Tracks', 'Sectors', 'Constant Sector Capacity', 'Variable Sector Density', 'Constant Angular Velocity', 'Disk Capacity', 'Disk Access Time', 'Seek Time', 'Rotational Latency', 'Transfer Time', 'Transfer Rate', 'Cylinder', 'Disk Addressing', 'Memory Hierarchy', 'Main Memory', 'RAM', 'ROM', 'SRAM', 'DRAM', 'Chip Select', 'DRAM Refresh']})