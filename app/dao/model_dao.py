from app.dao.db import get_connection

def get_models():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT name FROM Model"
            cursor.execute(sql)
            # fetchall returns a list of dictionaries
            models = cursor.fetchall()
            # Optionally extract just the name field
            return [model['name'] for model in models]
    finally:
        conn.close()

def get_metrics(model_name):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Assume you join on Model to get the correct modelId.
            sql = """
                SELECT m.name, met.accuracy, met.trainingShape
                FROM Model m
                JOIN Metric met ON m.modelId = met.modelId
                WHERE m.name = %s
            """
            cursor.execute(sql, (model_name,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_plots(model_name):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.auc, p.aucpr, p.shap
                FROM Model m
                JOIN Plot p ON m.modelId = p.modelId
                WHERE m.name = %s
            """
            cursor.execute(sql, (model_name,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_report(model_name):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT met.report
                FROM Model m
                JOIN Metric met ON m.modelId = met.modelId
                WHERE m.name = %s
            """
            cursor.execute(sql, (model_name,))
            return cursor.fetchone()
    finally:
        conn.close()
