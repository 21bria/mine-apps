class SqmsRouter:
    """
    A router to control all database operations on models in the
    sqms_apps and auth applications.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read sqms_apps and auth models go to sqms_db.
        """
        if model._meta.app_label in ['sqms_apps', 'auth']:
            return 'sqms_db'  # Ensure all related models are routed to sqms_db
        # Optionally, add handling for other apps here
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write sqms_apps and auth models go to sqms_db.
        """
        if model._meta.app_label in ['sqms_apps', 'auth']:
            return 'sqms_db'  # Ensure all writes are routed to sqms_db
        # Optionally, add handling for other apps here
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the sqms_apps or auth app is involved.
        """
        if obj1._meta.app_label in ['sqms_apps', 'auth'] or \
           obj2._meta.app_label in ['sqms_apps', 'auth']:
            return True
        # Allow relations with other apps or between different databases
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the sqms_apps and auth apps only appear in the 'sqms_db' database.
        """
        if app_label in ['sqms_apps', 'auth']:
            return db == 'sqms_db'  # Migrate only for 'sqms_db'
        # Handle migrations for other apps and databases here, if necessary
        return None

class GeosRouter:
    """
    A router to control all database operations on models in the
    geos_py and auth applications.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read geos_py and auth models go to geos_db.
        """
        if model._meta.app_label in ['geos_py', 'auth']:
            return 'geos_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write geos_py and auth models go to geos_db.
        """
        if model._meta.app_label in ['geos_py', 'auth']:
            return 'geos_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the geos_py or auth app is involved.
        """
        if obj1._meta.app_label in ['geos_py', 'auth'] or \
           obj2._meta.app_label in ['geos_py', 'auth']:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the geos_py and auth apps only appear in the 'geos_db' database.
        """
        if app_label in ['geos_py', 'auth']:
            return db == 'geos_db'
        return None
