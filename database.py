from sqlalchemy import create_engine, text
from config import DATABASE_URL

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
def store_topics(video_id: str, topics: list):
    with engine.begin() as connection:
        result = connection.execute(
            text("""SELECT id FROM subjects WHERE subject_name = :subject_name"""),
            {"subject_name": topics["subject"]}
            )
        subject_id = result.scalar()
        print ("subject_id", subject_id)

        
        for topic in topics["topics"]:
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
    get_topics("xyz1")
    # store_topics("xyz1",{'subject': 'Computer Organization & Architecture', 'topics': ['Magnetic Disk', 'Platters', 'Spindle', 'Read-Write Head', 'Arm Assembly', 'Tracks', 'Sectors', 'Constant Sector Capacity', 'Variable Sector Density', 'Constant Angular Velocity', 'Disk Capacity', 'Disk Access Time', 'Seek Time', 'Rotational Latency', 'Transfer Time', 'Transfer Rate', 'Cylinder', 'Disk Addressing', 'Memory Hierarchy', 'Main Memory', 'RAM', 'ROM', 'SRAM', 'DRAM', 'Chip Select', 'DRAM Refresh']})