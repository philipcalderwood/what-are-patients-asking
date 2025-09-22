#!/usr/bin/env python3
"""
Script to restore LLM_inferred_question values from old database backup
"""

import sqlite3
from pathlib import Path


def restore_llm_questions(current_db_path="data/mrpc.db", old_db_path="data/olddb.db"):
    """
    Restore LLM_inferred_question values from old database by matching on id
    """

    # Check if files exist
    if not Path(current_db_path).exists():
        print(f"❌ Current database not found: {current_db_path}")
        return False

    if not Path(old_db_path).exists():
        print(f"❌ Old database not found: {old_db_path}")
        return False

    try:
        # Connect to current database
        current_conn = sqlite3.connect(current_db_path)
        current_cursor = current_conn.cursor()

        # Connect to old database
        old_conn = sqlite3.connect(old_db_path)
        old_cursor = old_conn.cursor()

        # Get all records from old database with LLM_inferred_question
        print("📋 Fetching LLM_inferred_question values from old database...")
        old_cursor.execute("""
            SELECT id, LLM_inferred_question 
            FROM posts 
            WHERE LLM_inferred_question IS NOT NULL 
            AND LLM_inferred_question != ''
        """)
        old_records = old_cursor.fetchall()

        print(
            f"Found {len(old_records)} records with LLM_inferred_question in old database"
        )

        # Preview first 5 records
        print("\n🔍 Preview of records to update:")
        for i, (record_id, llm_question) in enumerate(old_records[:5]):
            print(f"  {record_id}: {llm_question[:100]}...")

        if len(old_records) > 5:
            print(f"  ... and {len(old_records) - 5} more records")

        # Ask for confirmation
        response = input("\n❓ Proceed with update? (y/N): ").strip().lower()
        if response != "y":
            print("❌ Update cancelled")
            return False

        # Update records one by one
        updated_count = 0
        failed_count = 0

        print("\n🔄 Updating records...")
        for record_id, llm_question in old_records:
            try:
                # Check if record exists in current database
                current_cursor.execute(
                    "SELECT id FROM posts WHERE id = ?", (record_id,)
                )
                if current_cursor.fetchone():
                    # Update the record
                    current_cursor.execute(
                        """
                        UPDATE posts 
                        SET LLM_inferred_question = ? 
                        WHERE id = ?
                    """,
                        (llm_question, record_id),
                    )
                    updated_count += 1

                    if updated_count % 100 == 0:
                        print(f"   Updated {updated_count} records...")

                else:
                    print(f"  ⚠️ Record {record_id} not found in current database")
                    failed_count += 1

            except Exception as e:
                print(f"  ❌ Failed to update record {record_id}: {e}")
                failed_count += 1

        # Commit changes
        current_conn.commit()

        print("\n Update complete!")
        print(f"  Updated: {updated_count} records")
        print(f"  ❌ Failed: {failed_count} records")

        # Close connections
        current_conn.close()
        old_conn.close()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Change to src directory if needed
    if Path.cwd().name != "src":
        src_path = Path(__file__).parent.parent
        if src_path.name == "src":
            import os

            os.chdir(src_path)
            print(f"📁 Changed to directory: {Path.cwd()}")

    restore_llm_questions()
