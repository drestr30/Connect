import os
from psycopg2.extensions import connection
import psycopg2
from dotenv import load_dotenv
import json

load_dotenv(".env", override=True)  # Load environment variables from .env file

def connect_db()-> connection:
    POSTGRES_REMOTE_ENDPOINT = os.environ['PGHOST']
    POSTGRES_REMOTE_USER = os.environ['PGUSER']
    POSTGRES_REMOTE_PASSWORD = os.environ['PGPASSWORD']
    POSTGRES_DB_NAME = os.environ['PGDATABASE']
    sslmode = "require"
    # logging.info(f"Env: {POSTGRES_REMOTE_ENDPOINT},{POSTGRES_DB_NAME},{POSTGRES_REMOTE_USER}")
    conn_string = f"host={POSTGRES_REMOTE_ENDPOINT} user={POSTGRES_REMOTE_USER} dbname={POSTGRES_DB_NAME} password={POSTGRES_REMOTE_PASSWORD} sslmode={sslmode}"

    conn: connection = psycopg2.connect(conn_string)
    return conn

def query_to_list(query, args=(), one=False):
    print('running query_to_list ...')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]

    conn.close()
    return (r[0] if r else None) if one else r

def start_session(selection: dict, selection_name: str, selection_hash: str) -> str:
    print('starting session ...')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO sessions (selection, selection_name, selection_hash) VALUES (%s, %s, %s) RETURNING id;",
                 (json.dumps(selection), selection_name, selection_hash))
    session_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id: str) -> dict:
    print('getting session ...')

    conn = connect_db()
    cur = conn.cursor()

    query = "SELECT * FROM sessions WHERE id = %s"
    row = query_to_list(query, (session_id,), one=True)
    conn.close()
    row['selection'] = json.loads(row['selection']) if row else None
    return row

def get_cards_by_hash(combination_hash: str, policy= 5) -> list:
    print('getting cards by hash ...')

    query = f"SELECT * FROM cards WHERE combination_hash = %s AND times_shown < {policy}"
    rows = query_to_list(query, (combination_hash,), one=False)

    return rows

def sample_cards_by_hash(combination_hash: str, sample_size: int = 10, policy = 5) -> list:
    print("sampling cards by hash ...")

    # Step 1: Weighted sampling query (no duplicates, freshness-aware)
    query = """
    WITH weighted AS (
        SELECT c.id, c.card_data, c.times_shown, c.like_count,
               GREATEST(0, %s - c.times_shown) AS weight
        FROM cards c
        WHERE c.combination_hash = %s
    ),
    scored AS (
        SELECT *,
               CASE
                   WHEN weight > 0 THEN -LN(RANDOM()) / weight
                   ELSE NULL
               END AS score
        FROM weighted
    )
    SELECT id, card_data, times_shown, like_count
    FROM scored
    WHERE score IS NOT NULL
    ORDER BY score DESC
    LIMIT %s;
    """

    # Fetch rows
    rows = query_to_list(query, (policy, combination_hash, sample_size), one=False)

    # if not rows:
    #     print("⚠️ No valid cards found, you should trigger generation here.")
    #     return []

    # # Step 2: Update times_shown for sampled cards
    # ids = tuple(r["id"] for r in rows)
    # update_query = """
    # UPDATE cards
    # SET times_shown = times_shown + 1,
    #     last_shown_at = NOW()
    # WHERE id = ANY(%s);
    # """
    # query_to_list(update_query, (list(ids),), one=True)

    return rows

def create_card(card_data: dict, combination_hash: str, combination_name: str) -> int:
    print('creating card ...')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO cards (card_data, combination_hash, combination_name) VALUES (%s, %s, %s) RETURNING id;",
                 (json.dumps(card_data), combination_hash, combination_name))
    card_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return card_id

def create_cards(card_data_list: list, combination_hash: str, combination_name: str) -> list:
    print('creating cards ...')

    conn = connect_db()
    cur = conn.cursor()

    card_ids = []
    for card_data in card_data_list:
        cur.execute("INSERT INTO cards (card_data, combination_hash, combination_name) VALUES (%s, %s, %s) RETURNING id;",
                     (card_data, combination_hash, combination_name))
        card_id = cur.fetchone()[0]
        card_ids.append(card_id)

    conn.commit()
    conn.close()
    return card_ids

def update_card_status(card_id: int, liked: bool = False):
    print('updating card status ...')

    conn = connect_db()
    cur = conn.cursor()

    if liked:
        cur.execute("""UPDATE cards SET 
                        times_shown = times_shown + 1,
                        like_count = like_count + 1
                        WHERE id = %s;""",
                        (card_id,))
    else:
        cur.execute("""UPDATE cards SET 
                        times_shown = times_shown + 1
                        WHERE id = %s;""",
                        (card_id,))

    conn.commit()
    conn.close()


def get_prompt_templates(selection_key: str, selection_value: str) -> list:
    print('getting prompt templates ...')

    query = "SELECT * FROM prompt_templates WHERE selection_key = %s AND selection_value = %s"
    rows = query_to_list(query, (selection_key, selection_value), one=False)
    return rows

if __name__ == "__main__":
    
    r = get_prompt_templates("social_context", "friends")
    print(r)    
