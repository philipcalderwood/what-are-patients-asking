from utilities.mrpc_database import MRPCDatabase
import pandas as pd


def get_forum_data(forum: str = "all", datatable_format: bool = False) -> pd.DataFrame:
    """Get forum data directly from database"""
    db = MRPCDatabase()
    try:
        if forum == "all":
            return db.get_all_posts_as_dataframe(datatable_format=datatable_format)
        else:
            # For specific forums, we need to filter after getting all data in datatable format
            if datatable_format:
                df = db.get_all_posts_as_dataframe(datatable_format=True)
                return df[df["forum"] == forum] if "forum" in df.columns else df
            else:
                return db.get_posts_by_forum(forum)
    except Exception as e:
        print(f"Error in get_forum_data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


def load_existing_feedback(data_id, inference_type):
    """Load existing feedback for a specific data point and inference type from SQLite database"""

    db = MRPCDatabase()
    return db.get_inference_feedback(data_id, inference_type)


def save_feedback_to_db(data_id, inference_type, rating, feedback_text, response_id):
    """Save feedback data to SQLite database"""
    from utilities.mrpc_database import MRPCDatabase

    db = MRPCDatabase()
    return db.save_inference_feedback(
        data_id, inference_type, rating, feedback_text, response_id
    )
