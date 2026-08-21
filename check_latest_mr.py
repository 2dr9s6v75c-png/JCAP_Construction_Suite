from core.database.connection import get_connection


def main():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr_number,
                status,
                workflow_status,
                assigned_to,
                current_assignment_id,
                created_at,
                CURRENT_TIMESTAMP,
                EXTRACT(
                    EPOCH FROM (
                        CURRENT_TIMESTAMP - created_at
                    )
                ) / 60.0 AS age_minutes
            FROM quotation.material_requests
            ORDER BY created_at DESC
            LIMIT 5
            """
        )

        rows = cur.fetchall()

        print()
        print("LATEST MATERIAL REQUESTS")
        print("=" * 100)

        if not rows:
            print("No Material Request records found.")
            return

        for index, row in enumerate(rows, start=1):
            print(f"Record #{index}")
            print(f"MR Number             : {row[0]}")
            print(f"Status                : {row[1]}")
            print(f"Workflow Status       : {row[2]}")
            print(f"Assigned To           : {row[3]}")
            print(f"Current Assignment ID : {row[4]}")
            print(f"Created At            : {row[5]}")
            print(f"Database Time         : {row[6]}")
            print(f"Age Minutes           : {row[7]}")
            print("-" * 100)

    except Exception as error:
        print()
        print("ERROR")
        print("=" * 100)
        print(str(error))

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()